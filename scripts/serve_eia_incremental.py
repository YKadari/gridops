from gridops.flows.eia_incremental import eia_incremental_flow


if __name__ == "__main__":
    eia_incremental_flow.serve(
        name="gridops-eia-hourly",
        interval=3600,
        tags=[
            "gridops",
            "eia",
            "incremental",
        ],
        description=(
            "Incrementally refreshes recent PJM "
            "hourly electricity demand data."
        ),
    )