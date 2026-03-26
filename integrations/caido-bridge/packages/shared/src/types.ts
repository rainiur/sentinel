export type SentinelRequest = {
  caidoRequestId: string;
  method: string;
  url: string;
  host: string;
  path: string;
  statusCode?: number;
  /** Serialized as ``req_headers_json`` on the Sentinel API */
  reqHeaders?: Record<string, string>;
  /** Serialized as ``resp_headers_json`` */
  respHeaders?: Record<string, string>;
};

export type SentinelFinding = {
  title: string;
  bugClass: string;
  severity?: string;
  confidence?: number;
  evidenceRefs?: string[];
};
