model_config_options = {
    "completions" : {
        "valid_format" : {
            "type" : "object",
            "required": ["model"], # 'model' property is required
            "properties" : {
                "model" : {
                    "type" : "string",
                    "enum": ["text-davinci-003", "text-davinci-002", "text-davinci-001", "text-curie-001", "text-babbage-001", "text-ada-001", "davinci", "curie", "babbage", "ada"] 
                },
                "temperature" : {
                    "type" : "number",
                    "minimum": 0,
                    "maximum": 2
                },
                "suffix" : {
                    "type" : "string"
                },
                "max_tokens" : {
                    "type" : "integer"
                },
                "top_p" : {
                    "type" : "number"
                },
                "n" : {
                    "type" : "integer",
                    "enum": [1]
                },
                "stream" : {
                    "type" : "boolean"
                },
                "logprobs" : {
                    "type" : "integer",
                    "maximum": 5
                },
                "echo" : {
                    "type" : "boolean"
                },
                "stop" : {
                    "type" : ["array", "string"]
                },
                "presence_penalty" : {
                    "type" : "number",
                    "minimum": -2.0,
                    "maximum": 2.0
                },
                "frequency_penalty" : {
                    "type" : "number",
                    "minimum": -2.0,
                    "maximum": 2.0
                },
                "best_of" : {
                    "type" : "integer"
                },
                "logit_bias" : {
                    "type" : "object"
                },
                "user" : {
                    "type" : "string"
                }
            }
        }
    },
    "chat" : {
        "valid_format" : {}
    }
}