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
  /** Human-readable line; folded into API ``bug_class`` with ``bugClass`` when both set */
  title: string;
  bugClass: string;
  /** Defaults to ``caido`` on the API */
  source?: string;
  severity?: string;
  confidence?: number;
  evidenceRefs?: string[];
};
