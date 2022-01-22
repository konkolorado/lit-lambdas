Lit-Lambdas
-----------

An AWS API Gateway that is backed by an AWS Lambda function which stores data in
DynamoDB-- all of which gets deployed and manageds via AWS CDK.

Usage
^^^^^

Development
===========

This project supports local development without access to AWS by using
localstack. To develop and run tests, first install the dependencies and begin
the backing services: 

``poetry install; just dependencies``

Note that this project runs commands using `just`_.

Now run the tests:

``just test``

Deployment
==========

This section covers creating all project resources on AWS. Running these
commands will deploy an unsecured APIGateway endpoint. If you do
this make sure to destroy the created stack to avoid charges. 

With an AWS profile active run:

``just deploy``

The output of this command will contain the API endpoint.

To remove the project:

``just destroy``

Dynamo
^^^^^^
The lambda's dynamo table enables the following access patterns:

* Get all of a user's actions
* Get an action by its action ID
* Get all of a user's actions by creation time
* Get all of a user's actions by completion time
* Get all of a user's actions by status

TODO
^^^^

* What kind of errors can the dynamo operations trigger?
* Decide on what the 'Action' should be
* Add pagination on queries that can return more than 1MB data

.. _just: https://github.com/casey/just