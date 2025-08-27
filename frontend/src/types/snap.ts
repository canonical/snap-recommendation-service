export type Snap = {
    snap_id: string;
    title: string;
    name: string;
    version: string;
    summary: string;
    description: string;
    icon: string;
    contact: string | null;
    publisher: string;
    revision: string;
    links: Array<{ [key: string]: string[] }>;
    media: Array<{
        name: string;
        height: number;
        type: string;
        url: string;
        width: number;
    }>;
    developer_validation: string;
    license: string;
    last_updated: string;
}