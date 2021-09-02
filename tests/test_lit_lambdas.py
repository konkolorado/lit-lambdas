from lit_lambdas.models import LambdaEvent


def test_model():
    assert LambdaEvent(**{"name": "hi"})
