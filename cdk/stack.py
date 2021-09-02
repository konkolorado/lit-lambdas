from pathlib import Path

import aws_cdk.aws_lambda as lambda_
from aws_cdk import core as cdk
from aws_cdk.aws_lambda_python import PythonFunction, PythonLayerVersion
from aws_cdk.aws_logs import RetentionDays


class LambdaStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cdk.Tags.of(self).add("StackName", construct_id)
        PythonFunction(
            self,
            "LitLambda",
            entry="./lit_lambdas",
            index="lit_lambdas/lambdas/index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            layers=[
                PythonLayerVersion(
                    self,
                    "LitLambdaLayer",
                    entry="./lit_lambdas",
                    compatible_runtimes=[lambda_.Runtime.PYTHON_3_8],
                )
            ],
            log_retention=RetentionDays.ONE_WEEK,
            timeout=cdk.Duration.seconds(3),
        )
