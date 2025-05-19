import time

from metaflow import project, FlowSpec, config_expr, Config, current
from metaflow.cards import Markdown

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

    def _query_snowflake(self, sql=None, template=None, card=False):
        if card and hasattr(current, "card"):

            def _out(txt):
                current.card.append(Markdown(txt))

        else:

            def _out(txt):
                pass

        if template:
            if isinstance(template, tuple):
                fname, args = template
            else:
                fname = template
                args = None

            with open(f"sql/{fname}.sql") as f:
                sql = (f.read(), args) if args else f.read()

        _out(f"## 🛢️ Executing SQL")
        _out(f"{sql}")

        from metaflow import Snowflake

        with Snowflake(integration=self.flowconfig.data.integration) as cn:
            with cn.cursor() as cur:
                t = time.time()
                if isinstance(sql, tuple):
                    cur.execute(*sql)
                else:
                    cur.execute(sql)
                secs = int(1000 * (time.time() - t))
                _out(f"Query finished in {secs}ms")
                return list(cur.fetchall())

    def _query_s3(self, card=False):

        from metaflow import S3

        if self.flowconfig.data_kwargs.check_mode == "files_metadata":
            # Mode 1: Watch for new files.
            # Return an object representing the S3 file system under s3://<bucket>/<key>
            with S3(
                role=self.flowconfig.data.role,
                s3root=self.flowconfig.data_kwargs.bucket,
            ) as s3:
                if self.flowconfig.data_kwargs.key and (
                    self.flowconfig.data_kwargs.key == ""
                    or self.flowconfig.data_kwargs.key == "/"
                ):
                    objects = s3.list_paths()
                else:
                    objects = s3.list_paths([self.flowconfig.data_kwargs.key])
                obj_metadata = []
                for obj in objects:
                    obj_metadata.append(
                        {
                            "key": obj.key,
                            "last_modified": obj.last_modified,
                            "size": obj.size,
                        }
                    )
                return obj_metadata
        elif self.flowconfig.data_kwargs.check_mode == "file_modified_ts":
            print("file_modified_ts")
            # Mode 2: Watch for the last time contents in a specific file were modified. Assumes key is path to that file, including extension.
            # Return an object representing the comparable data updated within the file.
            with S3(
                role=self.flowconfig.data.role,
                s3root=self.flowconfig.data_kwargs.bucket,
            ) as s3:
                s3obj = s3.get(self.flowconfig.data_kwargs.key)
                if s3obj.exists:
                    return s3obj.last_modified
                return None
        elif self.flowconfig.data_kwargs.check_mode == "file_size":
            print("file_size")
            # Mode 3: Watch for the size of contents in a specific file. Assumes key is path to that file, including extension.
            # Return an object representing the comparable data updated within the file.
            with S3(
                role=self.flowconfig.data.role,
                s3root=self.flowconfig.data_kwargs.bucket,
            ) as s3:
                s3obj = s3.get(self.flowconfig.data_kwargs.key)
                if s3obj.exists:
                    return s3obj.size
                return None
        else:
            raise ValueError(
                f"{self.flowconfig.data_kwargs.check_mode} is not supported. Use one of files_metadata, file_modified_ts, or file_size"
            )

    def query(self, storage_type, card=False, **kwargs):
        if storage_type == "snowflake":
            template = "sensor" if "template" not in kwargs else kwargs["template"]
            # TODO: Pick default smarter. Validate kwargs['template'] SQL file exists somewhere and is good SQL.
            return self._query_snowflake(template=template, card=card)
        elif storage_type == "s3":
            return self._query_s3(card=card)
        else:
            raise ValueError(
                f"Invalid storage_type in self.query {storage_type}. Supported options include ['snowflake','s3']."
            )

    # def query_s3(self, bucket=None, key=None, card=False):
    #     raise NotImplementedError
