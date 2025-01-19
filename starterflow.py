from metaflow import step, trigger_on_finish, current, project, Config, config_expr

from flowproject import BaseFlow, snowflake

@project(name=config_expr("flowconfig.project_name"))
@trigger_on_finish(flow='SensorFlow')
class StarterFlow(BaseFlow):

    @snowflake
    @step
    def start(self):
        self.timestamp = self.sensor_value
        print("Timestamp", self.timestamp)
        print(self.query_snowflake(template=('forecast', [self.timestamp])))
        self.next(self.end)
    
    @step
    def end(self):
        pass

if __name__ == '__main__':
    StarterFlow()
