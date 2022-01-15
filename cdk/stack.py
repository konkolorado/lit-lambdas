import aws_cdk.aws_lambda as lambda_
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_dynamodb as dynamo
from aws_cdk import core as cdk
from aws_cdk.aws_lambda_python import PythonFunction
from aws_cdk.aws_logs import RetentionDays


class LambdaStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        cdk.Tags.of(self).add("StackName", construct_id)

        table = dynamo.Table(
            self,
            "DynamoTable",
            table_name=None,
            partition_key=dynamo.Attribute(
                name="created_by", type=dynamo.AttributeType.STRING
            ),
            sort_key=dynamo.Attribute(
                name="action_id", type=dynamo.AttributeType.STRING
            ),
            billing_mode=dynamo.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="expires_at",
        )
        table.add_local_secondary_index(
            index_name="CreatedAtLSI",
            sort_key=dynamo.Attribute(
                name="created_at#id", type=dynamo.AttributeType.STRING
            ),
            projection_type=dynamo.ProjectionType.ALL,
        )
        table.add_local_secondary_index(
            index_name="CompletedAtLSI",
            sort_key=dynamo.Attribute(
                name="completed_at#id", type=dynamo.AttributeType.STRING
            ),
            projection_type=dynamo.ProjectionType.ALL,
        )
        table.add_local_secondary_index(
            index_name="ActionStatusLSI",
            sort_key=dynamo.Attribute(
                name="status#id", type=dynamo.AttributeType.STRING
            ),
            projection_type=dynamo.ProjectionType.ALL,
        )

        backend = PythonFunction(
            self,
            "LitLambdaHandler",
            entry="lit_lambdas",
            index="api/index.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            log_retention=RetentionDays.ONE_WEEK,
            timeout=cdk.Duration.seconds(3),
            environment={"APP_DYNAMO_TABLE_NAME": table.table_name},
        )
        table.grant_read_write_data(backend.grant_principal)

        api = apigateway.LambdaRestApi(
            self, "LitLambdaAPI", handler=backend, proxy=False
        )
        api.root.add_method("GET")  # GET /

        provider = api.root.add_resource("actions")
        provider.add_method("POST")  # POST /actions
        provider.add_method("GET")  # GET /actions

        single_action = provider.add_resource("{action_id}")
        single_action.add_method("DELETE")  # DELETE /actions/{action_id}
        single_action.add_method("GET")  # GET /actions/{action_id}
        single_action.add_method("PUT")  # PUT /actions/{action_id}
