import asyncio

import mcp_tools


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


class FakeDataStore:
    def get_ue_list(self):
        return ["100", "200"]

    def get_ue_reports(self, supi, limit=None):
        return [
            {
                "supi": supi,
                "notif_id": f"{supi}-old",
                "event": "REPORT",
                "timeStamp": 1,
                "customized_data": {
                    "Usage Report": {
                        "Volume": {"Uplink": 1, "Downlink": 2, "Total": 3},
                        "NoP": {"Total": 4},
                        "Duration": 5,
                        "Trigger": "periodic",
                    }
                },
            },
            {
                "supi": supi,
                "notif_id": f"{supi}-new",
                "event": "REPORT",
                "timeStamp": 2,
                "customized_data": {
                    "Usage Report": {
                        "Volume": {"Uplink": 10, "Downlink": 20, "Total": 30},
                        "NoP": {"Total": 40},
                        "Duration": 50,
                        "Trigger": "threshold",
                    }
                },
            },
        ]


def test_get_latest_reports_for_all_ues(monkeypatch):
    monkeypatch.setattr(mcp_tools, "data_store", FakeDataStore())

    mcp = FakeMCP()
    mcp_tools.register_mcp_tools(mcp)

    result = asyncio.run(mcp.tools["get_latest_reports_for_all_ues"]())

    assert "UE: 100" in result
    assert "UE: 200" in result
    assert "100-new" in result
    assert "200-new" in result
