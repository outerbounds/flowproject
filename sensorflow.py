from datetime import datetime
from itertools import islice

from metaflow import (
    step,
    config_expr,
    project,
    schedule,
    Parameter,
    card,
    Flow,
    current,
)
from metaflow.cards import Markdown
from metaflow.integrations import ArgoEvent

# custom module
from flowproject import BaseFlow #, snowflake

class SkipTrigger(Exception):
    pass


@project(name=config_expr("flowconfig.project_name"))
@schedule(cron=config_expr("flowconfig.sensor.cron_schedule"))
class SensorFlow(BaseFlow):
    """
    The SensorFlow will run in the Outerbounds dataplane.
    It acts like a gateway to the Outerbounds event bus.
    It is an implementation of the BaseFlow in /flowproject/baseflow.py.

    Before running this flow, check:
        1. /flowproject.toml: A configuration file to flip switches in this workflow.
        2. /flowproject/baseflow.py: An abstract class this flow inherits the self.query operation from.
    """

    force = Parameter("force-trigger", default=False)

    @card(type="blank")
    # @snowflake
    @step
    def start(self):
        """
        Set up cards for monitoring.
        Query the database metadata, determine whether the self.trigger should be run.
        The contract is that self.query returns a single object to compare run over run of this flow.
        if self.value == prev --> no change --> no events/trigger. else --> change --> trigger.
        """

        if self.force:
            current.card.append(Markdown("*Force is true - ignoring previous value*"))
            prev = None
        else:
            try:
                # The latest run is currently executing run so we have to pick the one
                # before this
                run = list(islice(Flow(current.flow_name), 2))[1]
                ago = (datetime.now() - run.finished_at).seconds // 60
                current.card.append(
                    Markdown(
                        f"Comparing to previous run **`{run.pathspec}`** from {ago} minutes ago"
                    )
                )
                prev = run["start"].task["value"].data
            except:
                current.card.append(Markdown(f"*Previous successful runs not found*"))
                prev = None

        # cleaner for Snowflake
        # [(self.value,)] = self.query(
        #     storage_type=self.flowconfig.data.storage_type,
        #     kwargs=self.flowconfig.data_kwargs,
        #     card=True
        # )

        # cleaner for s3
        self.value = self.query(
            storage_type=self.flowconfig.data.storage_type,
            kwargs=self.flowconfig.data_kwargs,
            card=True,
        )

        # print(f"Previous value {prev}, new value {self.value}")
        if self.value == prev:
            print("No changes.")
            self.trigger = False
            current.card.append(
                Markdown(f"## 🔄 No changes\n\nThe value is still `{self.value}`")
            )
        else:
            print("Triggering")
            self.trigger = True
            current.card.append(
                Markdown(
                    f"## 🚀 Value changed to `{self.value}`\n\nThe old value was `{prev}`"
                )
            )
        self.next(self.end)

    @step
    def end(self):
        "Dispatch the event."
        event_name = self.flowconfig.sensor.get("event_name")
        key = self.flowconfig.sensor.get("payload_key", "value")
        if event_name:
            print(f"Publishing event {event_name}")
            ArgoEvent(event_name).publish({key: self.value})
        else:
            if self.trigger:
                print("Finishing the run successfully to create an event")
            else:
                raise SkipTrigger(
                    "Not an error - failing this run on purpose "
                    "to avoid triggering flows downstream"
                )


if __name__ == "__main__":
    SensorFlow()
