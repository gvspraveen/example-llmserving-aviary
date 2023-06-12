# example-llmserving-aviary
Example Starting Code for LLM Serving with Aviary

This will only work on Anyscale.

## Running on Anyscale Workspaces
To run this on an Anyscale workspace, use the following steps:

1. Clone this repo to a workspace: `git clone https://github.com/anyscale/example-llmserving-aviary .`
2. Change directories into the aviary folder: `cd Aviary_Backend_Deployment`
3. Run the sample code: `serve run aviary.backend:llm_application models="models/"`

## Running on Anyscale Services
The backend can also be deployed to an Anyscale Service. Use the following steps:

1. Define a service yaml definition file
2. Deploy the service: `anyscale service rollout -f <yaml_definition.yaml>
3. Test the service.

## Notes
Additional information is available in the onboarding documentation.
