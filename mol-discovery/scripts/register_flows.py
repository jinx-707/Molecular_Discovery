#!/usr/bin/env python3
from prefect.deployments import Deployment
from backend.flows.discovery_flow import discovery_pipeline
from backend.flows.feedback_flow import feedback_loop
from backend.flows.scheduled_flows import weekly_retrain

def register_all():
    # Discovery deployment
    Deployment.build_from_flow(
        flow=discovery_pipeline,
        name="discovery-pipeline",
        work_queue_name="ml-queue"
    ).apply()
    
    # Feedback deployment
    Deployment.build_from_flow(
        flow=feedback_loop,
        name="feedback-loop",
        work_queue_name="ml-queue"
    ).apply()
    
    print("✅ Flows registered! Run 'prefect server start' then 'prefect agent local --queue ml-queue'")

if __name__ == "__main__":
    register_all()

