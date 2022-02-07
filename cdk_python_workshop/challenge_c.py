import requests

from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    aws_ec2 as ec2,
)

from constructs import Construct


ISOLATED_SUBNET_KEY = "/example/vpc/isolated-subnet-{}-id"


class ChallengeCStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # Use "value_for_string_parameter" to get the value during synth
        # "from_string_parameter_name" will only return a !Ref token which is not good enough
        vpc_id = ssm.StringParameter.value_for_string_parameter(
            self, parameter_name="/example/vpc/vpc-id"
        )

        # The L2 VPC construct is very powerful. We can define all subnets here too!
        vpc = ec2.Vpc.from_vpc_attributes(
            self,
            "Vpc",
            availability_zones=["eu-west-1a", "eu-west-1b", "eu-west-1c"],
            vpc_id=vpc_id,
            # Uses a for loop to find all subnets for certain SSM parameters.
            isolated_subnet_ids=[
                ssm.StringParameter.value_for_string_parameter(
                    self, parameter_name=ISOLATED_SUBNET_KEY.format(i)
                )
                for i in range(1, 4)
            ],
        )

        # DO NOT USE THE SPECIAL DATABASE SECRET IN SECRETS MANAGER.
        # It must be a custom secret, using key/value combo in JSON format.
        # See here for correct formatting of secret:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_rds.Credentials.html#static-fromwbrpasswordusername-password
        database_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "DatabaseSecret", secret_name="database-secret-1Y2H5E"
        )

        # Call random.org and get the random number, between 1 and 6
        response = requests.get(
            "https://www.random.org/integers/",
            params={
                "num": "1",
                "min": "1",
                "max": "6",
                "col": "1",
                "base": "10",
                "format": "plain",
            },
        )

        if response.status_code != 200:
            raise RuntimeError("No valid status")

        # Take the response from random.org and format it as an int
        random_instance_number = int(response.content.strip())

        aurora_cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_13_4
            ),
            credentials=rds.Credentials.from_secret(
                secret=database_secret, username="rds_admin"
            ),
            instance_props=rds.InstanceProps(
                # Note that many Landing Zones will create an RDS subnet group for you.
                # In this case, fetch the name from SSM parameters and use property subnet_group
                vpc_subnets=ec2.SubnetType.PRIVATE_ISOLATED,
                vpc=vpc,
                instance_type=ec2.InstanceType(
                    instance_type_identifier="t4g.medium"
                ),
            ),
            instances=random_instance_number,
            # Don't set DESTROY on production. It helps speed up deletion of the cluster.
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Finally, write out the endpoints to SSM
        ssm.StringParameter(
            self,
            "myWriterEndpoint",
            parameter_name="/example/challenge_c/writer_endpoint",
            string_value=aurora_cluster.cluster_endpoint.socket_address,
        )

        ssm.StringParameter(
            self,
            "myReaderEndpoint",
            parameter_name="/example/challenge_c/reader_endpoint",
            string_value=aurora_cluster.cluster_read_endpoint.socket_address,
        )
