from prefect import flow
from prefect.schedules import CronSchedule
from prefect.deployments import Deployment
from .discovery_flow import discovery_pipeline
from .feedback_flow import feedback_loop

# Weekly retraining
weekly_retrain = CronSchedule("0 2 * * 0")  # Sunday 2AM

deployment = Deployment.build_from_flow(
    flow=feedback_loop,
    name="weekly-retrain",
    schedule=weekly_retrain,
    work_queue_name="ml-queue"
)

if __name__ == "__main__":
    deployment.apply()
    print("Scheduled weekly retraining")

# Daily ingestion (stub)
@flow
def daily_ingestion():
    print("Ingesting new data from BRENDA/MaterialsProject...")

