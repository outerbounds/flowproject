from metaflow import project, FlowSpec, config_expr, Config, current

try:
    # Python > 3.10
    import tomllib

    toml_parser = "tomllib.loads"
except ImportError:
    # Python < 3.10
    # pip install toml
    toml_parser = "toml.loads"


class BaseFlow(FlowSpec):
    flowconfig = Config("flowconfig", default="flowproject.toml", parser=toml_parser)

    @property
    def sensor_value(self):
        try:
            return current.trigger.run.data.value
        except:
            pass

    def query_snowflake(self, sql=None, template=None):

        if template:
            if isinstance(template, tuple):
                fname, args = template
            else:
                fname = template
                args = None

            with open(f'sql/{fname}.sql') as f:
                sql = (f.read(), args) if args else f.read()

        from metaflow import Snowflake
        with Snowflake(integration=self.flowconfig.data.integration) as cn:
            with cn.cursor() as cur:
                if isinstance(sql, tuple):
                    cur.execute(*sql)
                else:
                    cur.execute(sql)
                return list(cur.fetchall())
