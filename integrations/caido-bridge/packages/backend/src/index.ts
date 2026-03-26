// TODO: Replace with actual Caido backend SDK imports.
// This file is a scaffold for bridge logic between Caido and Sentinel API.

export {
  pushFindingsToSentinel,
  pushRequestsToSentinel,
  type SentinelBridgeConfig,
} from './sentinel-sync';

export async function registerSentinelBackend(): Promise<void> {
  console.log('Sentinel backend plugin scaffold loaded');
  // TODO:
  // - register sync commands using Caido SDK (selected HTTP requests → SentinelRequest[])
  // - call pushRequestsToSentinel(cfg, requests) — see packages/backend/src/sentinel-sync.ts
  // - add signed callback verification (TASKS §3)
  // - optionally trigger approved workflows
}
