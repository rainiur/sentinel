export type SentinelRequest = {
  caidoRequestId: string;
  method: string;
  url: string;
  host: string;
  path: string;
  statusCode?: number;
  reqHeaders?: Record<string, string>;
  respHeaders?: Record<string, string>;
};

export type SentinelFinding = {
  title: string;
  bugClass: string;
  severity?: string;
  confidence?: number;
  evidenceRefs?: string[];
};
