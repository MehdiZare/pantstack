import json
import os
import uuid

from stack.libs.shared.aws import client as aws_client


class EventBridgePublisher:
    def __init__(self, bus_name: str, source: str = "services.web"):
        self.bus_name = bus_name
        self.source = source
        self.events = aws_client("events")

    @classmethod
    def from_env(cls) -> "EventBridgePublisher":
        name = os.getenv("EVENT_BUS_NAME")
        if not name:
            raise RuntimeError("EVENT_BUS_NAME not configured")
        return cls(bus_name=name)

    def publish(self, job_type: str, params: dict) -> str:
        cid = str(uuid.uuid4())
        detail = {"job_type": job_type, "params": params, "correlation_id": cid}
        self.events.put_events(
            Entries=[
                {
                    "EventBusName": self.bus_name,
                    "Source": self.source,
                    "DetailType": "jobs.requested",
                    "Detail": json.dumps(detail, default=str),
                }
            ]
        )
        return cid
