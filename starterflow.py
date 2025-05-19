from metaflow import step, trigger_on_finish, current, project, Config, config_expr

from flowproject import BaseFlow  # , snowflake


@project(name=config_expr("flowconfig.project_name"))
@trigger_on_finish(flow="SensorFlow")
class StarterFlow(BaseFlow):

    # @snowflake
    @step
    def start(self):

        print(f"{'*'*6}\nCONFIG\n{'*'*6}\n{self.flowconfig}\n{'*'*6}\n")
        naughty_points = 0
        if self.flowconfig.sensor.event_name == "":
            naughty_points += 1
            print("Event name not specified! Experiment with flowproject.toml.")
        if self.flowconfig.data.type not in ["snowflake", "s3"]:
            naughty_points += 5
            print(
                "Woah there, partner. This template only supports Snowflake and S3 for now."
            )
        if (
            self.flowconfig.data.type == "snowflake"
            and "template" not in self.flowconfig.data_kwargs
        ):
            naughty_points += 3
            print(
                "When you run the Snowflake SensorFlow, you need a SQL query defined in /sql, and to reference that in the data_kwargs."
            )
        if (
            self.flowconfig.data.type == "s3"
            and "bucket" not in self.flowconfig.data_kwargs
        ):
            naughty_points += 3
            print(
                "When you run the S3 SensorFlow, you need a bucket defined in the data_kwargs.bucket variable."
            )
        if (
            self.flowconfig.data.type == "s3"
            and "key" not in self.flowconfig.data_kwargs
        ):
            naughty_points += 3
            print(
                "When you run the S3 SensorFlow, you need a bucket key defined in the data_kwargs.key variable."
            )

        if naughty_points < 5:
            print("Nice config you've got there.")
        else:
            print(
                "Your config is horribly messed up. Possibly beyond repair. Commit authors take no responsibility for how you arrived in this mess."
            )

        self.value = self.query(
            storage_type=self.flowconfig.data.type, kwargs=self.flowconfig.data_kwargs
        )

        print(f"Query result: {self.value}")
        print(
            "All done! This flow doesn't do that much beyond show you how to get started with the moving parts here."
        )
        print(
            "Before moving on to the sensorflow.py, check out /flowproject/baseflow.py and /flowproject.toml."
        )
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    StarterFlow()
