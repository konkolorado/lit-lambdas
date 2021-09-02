from aws_cdk import core as cdk

from stack import LambdaStack


class LambdaApp(cdk.App):
    def __init__(self):
        super().__init__()
        LambdaStack(self, "LitLambdaStack")


LambdaApp().synth()
