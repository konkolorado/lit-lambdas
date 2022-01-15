Lit-Lambdas
-----------

An AWS Lambda function template that gets deployed via AWS CDK.

Dynamo
^^^^^^
The lambda's dynamo table enables the following access patterns:
- Get all of a user's actions
- Get a user's action by its action ID
- Get all of a user's actions by creation time
- Get all of a user's actions by completion time
- Get all of a user's actions by status


TODO
^^^^

- What kind of errors can the dynamo operations trigger?
- Decide on what the 'Action' should be
