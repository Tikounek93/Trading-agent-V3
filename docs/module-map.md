# Module map

This is the implementation map for v3. A module is complete only when its
declared scope, contracts, implementation and reusable tests are complete.

| Module | Version | Status | Responsibility |
| --- | --- | --- | --- |
| `system_core` | `0.1.0` | candidate | Lifecycle, modes, readiness, dependencies and run manifests. |
| `source_intake` | `1.1.0` | stable | Register sources, acquire video/metadata/subtitles, inspect artifacts and calculate readiness. |
| `data_platform` | `0.2.0` | candidate | Durable artifact storage, promotion and SQLite source catalog. |
| `frontend` | `0.3.0` | candidate | Operator workspace with module navigation, source intake, knowledge explorer and correction review. |
| `knowledge_processing` | `1.0.0` | stable | Prepare, validate and persist structured advisory knowledge from source artifacts. |
| `strategy_blueprint` | planned | planned | Derive a controlled description of required strategy agents, tools and flows. |
| `strategy_engine` | planned | planned | Build and evaluate setup candidates from approved strategy inputs. |
| `market_data` | planned | planned | Receive and normalize market data from providers. |
| `market_analysis` | planned | planned | Find market objects and determine their relevance and context. |
| `external_context` | planned | planned | Add external context such as news and no-trade conditions. |
| `execution` | planned | planned | Confirm setup candidates and submit approved orders through an adapter. |
| `trade_management` | planned | planned | Manage active trades, stops, targets and invalidation rules. |
| `trading_journal` | planned | planned | Archive completed, cancelled and invalidated trades. |
| `decision_journal` | planned | planned | Preserve decision reasoning and evaluation context separately from system logs. |
| `feedback_analysis` | planned | planned | Compare journal outcomes and produce analysis for human-led iteration. |

The planned names are working names. Changing a name requires updating this
map, the affected contracts and the relevant decision record before code is
moved.
