# Fine Tuning API
The Fine Tuning API allows you to fine tune various open source LLMs on your own data, then make inference calls to the resulting LLM. For more specific details, see the [python client docs](../api/python_client.md).

## Preparing Data
Your data must be formatted as a CSV file that includes two columns: `prompt` and `response`. The data needs to be uploaded to somewhere publicly accessible, so that we can read the data to fine tune on it. For example, you can upload your data to a public s3 bucket.

## Launching the Fine Tune
Once you have uploaded your data, you can use our API to launch a Fine Tune. You will need to provide the base model to train off of, the locations of the training and validation files, an optional set of hyperparameters to override, and an optional suffix to append to the name of the fine tune. 

See the [Model Zoo](../model_zoo) to see which models have fine tuning support.

Once the fine tune is launched, you can also get the status of your fine tune.

## Making inference calls to your fine tune

Once the fine tune is finished, you will be able to start making requests to the model. First, you can list the available LLMs in order to get the name of your fine tuned model. See the [completions API](completions) for more details. You can then use that name to direct your inference requests.