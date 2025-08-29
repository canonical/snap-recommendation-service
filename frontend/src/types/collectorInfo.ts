export type CollectorStep = {
    name: string;
    success: boolean;
    last_successful_run: string;
    last_failed_run: string;
    id: string;
}

export type CollectorInfo = {
    pipeline_steps: CollectorStep[];
    last_updated: string;
}