PROJECT_NAME = "AviaryFrontend"

NUM_LLM_OPTIONS = 3

# (connect, read) timeouts in seconds. we make the "read" timeout deliberately
# shorter than in cloudfront OR gradio, so that we can explicitly handle timeouts.
TIMEOUT = (5, 40)

AVIARY_DESC = """

# What is this?

Aviary allows you to take a single prompt and send it to a number of open source LLMs
hosted by Anyscale. It also gives you estimates of the cost as well as the latency.

It is built on top of [Ray](https://ray.io) by the company
[Anyscale](https://anyscale.com).

It is an open source project and you can launch your own instance of aviary.backend.

If you would like to use a managed version of Aviary specific to your company,
please let mwk@anyscale.com know.

# Notes

## Win Ratio

The "win Ratio" shows the relative performance of different LLMs. Higher is better,
with the perfect
score (beats all other algorithms 100 per cent of the time) being 3000.
If you were to randomly pick which answer is best, that would result in a
win ratio of 1000.


## Cost

The cost is calculated assuming it is using an on-demand AWS g5.xlarge instance at
list prices.
It also doesn't include the benefits of batching (which can't be guaranteed).
Hence it can be considered an upper bound on the cost.
"""

EXAMPLES_QA = [
    "How do I make fried rice? ",
    "What are the 5 best sci fi books? ",
    "What are the best places in the world to visit? ",
    "Which Olympics were held in Australia?",
]

EXAMPLES_IF = [
    "Please describe a beautiful house.",
    "Generate 5 second grade level math problems.",
]

EXAMPLES_ST = [
    "Once upon a time, ",
    "It was the worst of times, it was the best of times. ",
]

MODELS = {
    "CarperAI/stable-vicuna-13b-delta": "This is a model based on Vicuna but with reinforcement learning with human "
    "feedback applied. Pretty Good. Based on LLaMa so non-commercial use only. "
    "13B parameters.",
    "lmsys/vicuna-13b-delta-v1.1": "LLaMA with additional training on records from ChatGPT. One of the best. "
    "Based on LLaMa so non-commercial use only. 13B Parameters.",
    "stabilityai/stablelm-tuned-alpha-7b": "Model trained with large window (4096 tokends). Works OK for summarization. "
    "Tuned for instruction following. CC-BY-SA license.",
    "mosaicml/mpt-7b-instruct": "TODO",
    "eachadea/ggml-vicuna-13b-1.1": "TODO",
    "amazon/LightGPT": "TODO",
    "diegi97/dolly-v2-12b-sharded-bf16": "TODO",
    "RWKV/rwkv-raven-14b": "TODO",
    "mosaicml/mpt-7b-chat": "TODO",
    "mosaicml/mpt-7b-storywriter": "TODO",
    "h2oai/h2ogpt-oasst1-512-12b": "TODO",
    "OpenAssistant/oasst-sft-7-llama-30b-xor": "TODO",
}

SELECTION_DICT = {
    "Fast LLMs": [
        "amazon/LightGPT",
        "mosaicml/mpt-7b-instruct",
        "mosaicml/mpt-7b-chat",
    ],
    "LLM Tunes": [
        "mosaicml/mpt-7b-instruct",
        "mosaicml/mpt-7b-chat",
        "mosaicml/mpt-7b-storywriter",
    ],
    "Random selection": [],
}


MODEL_DESCRIPTIONS_HEADER = "# Model Descriptions\n\n"

MODEL_DESCRIPTION_FORMAT = "## [{model_id}]({model_url})\n{model_description}"

HEADER = """# \U0001f99c \U0001f50d Aviary: _A place to study stochastic parrots_
"""

CSS = """
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  border-radius: 2px;
}
::-webkit-scrollbar-thumb {
  background: #bfdbfe;
  border-radius: 4px;
}
body, gradio-app {
    height: 100vh;
    max-height: 100vh;
}
.pill-button {
    border-radius: 32px !important;
    border: none !important;
}
.main,
.contain,
#component-0,
#top-tab-group > div,
#top-tab-group > div > div,
#left-column,
#right-column,
.output-text > label,
.output-text > label > textarea {
    height: 100% !important;
}

.contain,
#component-0,
#component-0 > .tabs,
#top-tab-group,
#top-tab-group > div {
    overflow: hidden !important;
}

#top-tab-group {
    padding: 16px !important;
}
#top-tab-group > div > div {
    gap: 48px !important;
}

#left-column,
#right-column {
    overflow: auto;
    padding-right: 12px;
}

#left-column-content,
#right-column-content {
    flex-wrap: nowrap;
}

#prompt,
#left-column-content > .form,
.llm-selector {
    background: none !important;
    padding: 0 !important;
    border: none !important;
}
#left-column-content label > span {
    font-weight: bold;
    font-size: 1rem;
}

#prompt-examples > .gallery > button {
    opacity: .5;
}
#prompt-examples > .gallery > button:hover {
    opacity: 1;
}

#right-column-content {
    gap: 24px;
}
#right-column-content > .compact,
#right-column-content > .compact > .compact,
#right-column-content > .compact > .compact > .block {
    padding: 0 !important;
    background: none !important;
    border: none !important;
}
#right-column-content > div {
    flex-grow: 1 !important;
}

.output-container {
    position: relative;
    gap: 8px !important;
}
.rank-button {
    flex-grow: 0 !important;
    white-space: nowrap;
    line-height: 16px !important;
    padding: 4px 12px !important;
    font-size: .8rem !important;
    font-weight: normal !important;
    min-width: fit-content !important;
}
.output-content {
    flex-grow: 1 !important;
}
.output-content > .form {
    flex-grow: 3 !important;
    border: none !important;
}
.output-content > .output-stats {
    flex-grow: 1 !important;
}
.output-stats > table {
    width: 100% !important;
}
.output-stats td,
.output-stats th {
    padding: 0 !important;
    color: #aaa !important;
}
.output-stats th,
.output-stats td {
    border-bottom-color: #aaa !important;
}
.output-text {
    padding: 0 !important;
    background: none !important;
}

#leaderboard-tab {
    overflow: auto;
}
#refresh-leaderboard-button {
    margin-top: 12px;
}

"""
# Database to be used for Mongo DB
DB_NAME = "aviary"

# Name of collection in Mongo DB
COLLECTION_NAME = "event_log"

G5_COST_PER_S_IN_DOLLARS = 1.006 / 60 / 60
