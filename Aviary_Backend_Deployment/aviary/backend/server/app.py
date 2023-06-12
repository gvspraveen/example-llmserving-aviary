import asyncio
import traceback
from typing import Any, Dict, List, Optional, Union

import ray
import ray.util
from fastapi import FastAPI
from ray import serve
from ray.exceptions import RayActorError
from ray.serve.deployment import ClassNode

from aviary.backend.llm.predictor import LLMPredictor
from aviary.backend.logger import get_logger
from aviary.backend.server._batch import QueuePriority, _PriorityBatchQueue, batch
from aviary.backend.server.models import (
    Args,
    DeepSpeed,
    Prompt,
)

logger = get_logger(__name__)

app = FastAPI()


@serve.deployment(
    autoscaling_config={
        "min_replicas": 1,
        "initial_replicas": 2,
        "max_replicas": 8,
    },
    max_concurrent_queries=2,  # Maximum backlog for a single replica
    health_check_period_s=10,
    health_check_timeout_s=30,
)
class LLMDeployment(LLMPredictor):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.args = None
        super().__init__()

    def _should_reinit_worker_group(self, new_args: Args) -> bool:
        old_args = self.args

        if not old_args:
            return True

        old_scaling_config = self.args.air_scaling_config
        new_scaling_config = new_args.scaling_config.as_air_scaling_config()

        if not self.base_worker_group:
            return True

        if old_scaling_config != new_scaling_config:
            return True

        if not old_args:
            return True

        if old_args.model_config.initialization != new_args.model_config.initialization:
            return True

        if (
            old_args.model_config.generation.max_batch_size
            != new_args.model_config.generation.max_batch_size
            and isinstance(new_args.model_config.initialization.initializer, DeepSpeed)
        ):
            return True

        # TODO: Allow this
        if (
            old_args.model_config.generation.prompt_format
            != new_args.model_config.generation.prompt_format
        ):
            return True

        return False

    async def reconfigure(
        self,
        config: Union[Dict[str, Any], Args],
        force: bool = False,
    ) -> None:
        logger.info("Reconfiguring...")
        if not isinstance(config, Args):
            new_args: Args = Args.parse_obj(config)
        else:
            new_args: Args = config

        should_reinit_worker_group = force or self._should_reinit_worker_group(new_args)

        self.args = new_args
        if should_reinit_worker_group:
            await self.rollover(self.args.air_scaling_config)
        logger.info("Reconfigured.")

    @property
    def max_batch_size(self):
        return self.args.model_config.generation.max_batch_size

    @property
    def batch_wait_timeout_s(self):
        return self.args.model_config.generation.batch_wait_timeout_s

    def get_max_batch_size(self):
        return self.max_batch_size

    def get_batch_wait_timeout_s(self):
        return self.batch_wait_timeout_s

    @app.get("/metadata")
    async def metadata(self) -> dict:
        return self.args.dict(
            exclude={
                "model_config": {"initialization": {"s3_mirror_config", "runtime_env"}}
            }
        )

    @app.post("/")
    async def generate_text(self, prompt: Prompt):
        text = await self.generate_text_batch(
            prompt, priority=QueuePriority.GENERATE_TEXT
        )
        return text

    @app.post("/batch")
    async def batch_generate_text(self, prompts: List[Prompt]):
        texts = await asyncio.gather(
            *[
                self.generate_text_batch(
                    prompt, priority=QueuePriority.BATCH_GENERATE_TEXT
                )
                for prompt in prompts
            ]
        )
        return texts

    @batch(
        max_batch_size=get_max_batch_size,
        batch_wait_timeout_s=get_batch_wait_timeout_s,
        batch_queue_cls=_PriorityBatchQueue,
    )
    async def generate_text_batch(self, prompts: List[Prompt]):
        """Generate text from the given prompts in batch"""
        if not prompts or prompts[0] is None:
            return prompts
        logger.info(f"Received {len(prompts)} prompts {prompts}")
        data_ref = ray.put(prompts)

        try:
            prediction = await self._predict_async(data_ref)
        except RayActorError:
            logger.warning(
                f"Prediction failed due to RayActorError. "
                f"Traceback:\n{traceback.print_exc()}"
            )
            await self.check_health()
            prediction = await self._predict_async(data_ref)

        logger.info(f"Predictions {prediction}")
        if not isinstance(prediction, list):
            return [prediction]
        return prediction[: len(prompts)]

    # Called by Serve to check the replica's health.
    async def check_health(self):
        if self._new_worker_group_lock.locked():
            logger.info("Rollover in progress, skipping health check")
            return
        if self.pg and self.base_worker_group:
            dead_actors = []
            for actor in self.base_worker_group:
                actor_state = ray.state.actors(actor._ray_actor_id.hex())
                if actor_state["State"] == "DEAD":
                    dead_actors.append(actor)
            if dead_actors:
                logger.warning(
                    f"At least one prediction worker is dead. Dead workers: {dead_actors}. "
                    "Reinitializing worker group."
                )
                await self.rollover(self.args.air_scaling_config)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}:{self.args.model_config.model_id}"


def _replace_prefix(model: str) -> str:
    return model.replace("--", "/")


@serve.deployment(
    route_prefix="/",
)
@serve.ingress(app)
class RouterDeployment:
    def __init__(
        self, models: Dict[str, ClassNode], model_configurations: Dict[str, Args]
    ) -> None:
        self._models = models
        # TODO: Remove this once it is possible to reconfigure models on the fly
        self._model_configurations = model_configurations

    @app.post("/query/{model}")
    async def query(self, model: str, prompt: Prompt) -> Dict[str, Dict[str, Any]]:
        model = _replace_prefix(model)
        results = await asyncio.gather(
            *(await asyncio.gather(*[self._models[model].generate_text.remote(prompt)]))
        )
        results = results[0]
        logger.info(results)
        return {model: results}

    @app.post("/query/batch/{model}")
    async def batch_query(
        self, model: str, prompts: List[Prompt]
    ) -> Dict[str, List[Dict[str, Any]]]:
        model = _replace_prefix(model)
        results = await asyncio.gather(
            *(
                await asyncio.gather(
                    *[self._models[model].batch_generate_text.remote(prompts)]
                )
            )
        )
        results = results[0]
        logger.info(results)
        return {model: results}

    @app.get("/metadata/{model}")
    async def metadata(self, model) -> Dict[str, Dict[str, Any]]:
        model = model.replace("--", "/")
        # This is what we want to do eventually, but it looks like reconfigure is blocking
        # metadata = await asyncio.gather(
        #     *(await asyncio.gather(*[self._models[model].metadata.remote()]))
        # )
        # metadata = metadata[0]
        metadata = self._model_configurations[model].dict(
            exclude={
                "model_config": {"initialization": {"s3_mirror_config", "runtime_env"}}
            }
        )
        logger.info(metadata)
        return {"metadata": metadata}

    @app.get("/models")
    async def models(self) -> List[str]:
        return list(self._models.keys())
