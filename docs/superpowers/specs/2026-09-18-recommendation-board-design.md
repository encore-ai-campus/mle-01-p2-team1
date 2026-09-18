# Recommendation Board Design

## Goal

Replace only the festival recommendation page with a data-backed filter board. The page must show real region, theme, period, audience, and fee values; support recommendation presets; and display at most four festival cards.

## Scope

- Modify the recommendation page rendered by `render_recommendations`.
- Enrich festival records with recommendation metadata while loading existing local data.
- Add pure recommendation filtering and ranking logic plus automated tests.
- Preserve the home, map, detail, chatbot, and knowledge-graph page layouts and behavior.
- Do not add a hero image to the recommendation page.

## Data model and enrichment

`load_app_data` will continue to return the existing `festivals`, `triples`, and `documents` collections. Each festival record will additionally expose normalized recommendation fields derived from current artifacts:

- `region`: a short province or metropolitan-city name derived from the festival address.
- `themes`: all `HAS_THEME` objects whose `source_doc_ids` contain the festival `doc_id`.
- `audiences`: normalized audience categories derived from `TARGETS` objects and `age_limit`.
- `fee_category`: `무료` or `유료`, derived from `usage_fee`.
- `relation_count`: the number of knowledge-graph triples connected to the festival document.

Theme and audience values are joined by matching a festival `doc_id` to every triple value in `source_doc_ids`. Empty values are retained internally but excluded from filter options, so `미분류` never appears in a dropdown.

Audience normalization produces the stable categories `전 연령`, `어린이`, `청소년`, `성인`, `가족`, and `시니어`. Keyword matches in `TARGETS` and `age_limit` may assign multiple categories to one festival. A festival with explicit all-ages wording is assigned `전 연령`.

Fee normalization uses these rules:

- `무료`: the source indicates free entry and contains no paid amount or paid-program wording.
- `유료`: the source says `유료`, contains a won amount, or indicates that any portion or program is paid.
- Missing fee data is not offered as a filter option and does not match either fee filter.

## Recommendation logic

A focused recommendation module will provide pure functions for option construction, filtering, preset selection, and ranking. It receives festival dictionaries and an injectable reference date so date behavior is deterministic in tests.

All filters combine with AND semantics:

- Region matches normalized `region` exactly.
- Theme matches one entry in `themes` exactly.
- Period matches a month intersecting the inclusive start-to-end date range.
- Audience matches one entry in `audiences` exactly.
- Fee matches `fee_category` exactly.

Recommendation presets behave as follows:

- `전체`: apply the selected filters and sort by start date, then festival name.
- `인기`: apply the selected filters and sort by descending `relation_count`, then start date and name.
- `이번 달`: keep festivals whose inclusive event range intersects the reference date's calendar month.
- `곧 시작`: keep festivals starting from the reference date through 30 days later, inclusive.
- `가족 추천`: keep festivals assigned `가족`, `어린이`, or `전 연령`.

After filtering and preset ranking, the page displays only the first four records. The total matched count may be shown separately so users know additional results exist.

## Recommendation page UI

The recommendation page uses native Streamlit controls and keeps the existing application navigation unchanged.

1. A compact title and explanatory caption replace any image-led header.
2. A bordered filter container contains region, theme, period, and audience selectboxes in a responsive two-row or four-column layout.
3. A single-select fee control appears below them with `전체`, `무료`, and `유료`.
4. A single-select recommendation control appears above the results with `전체`, `인기`, `이번 달`, `곧 시작`, and `가족 추천`.
5. Results render as a two-column grid of at most four cards. Each card shows festival name, region, formatted dates, fee text, a small set of theme and audience badges, and the existing detail navigation action.
6. When no festival matches, the page displays a clear empty state without changing the selected filters.

The page will use sentence-case Korean labels and Streamlit-native containers and selection widgets. CSS changes, if required for card polish, remain scoped to the recommendation page and do not alter other pages.

## Error handling

- Malformed or absent triples produce empty enrichment collections without preventing festivals from rendering.
- Invalid dates do not match month-based presets or filters.
- Missing address, theme, audience, or fee values never create a `미분류` option.
- A festival with incomplete metadata can still appear under `전체` when the populated filters do not exclude it.

## Testing

Automated tests will cover:

- Joining `HAS_THEME` and `TARGETS` triples to festivals by `source_doc_ids`.
- Region, audience, and fee normalization, including partially paid festivals.
- Dropdown option construction without `미분류`.
- AND-combined filters for region, theme, month, audience, and fee.
- `인기`, `이번 달`, `곧 시작`, and `가족 추천` preset behavior.
- Stable ranking and the four-card display limit.
- A Streamlit-level recommendation-page smoke test confirming the intended controls render.

## Success criteria

- Recommendation dropdowns contain real values from the current data and never show `미분류`.
- Fee selection has `전체`, `무료`, and `유료` and changes the visible results.
- All five recommendation presets return data when matching records exist.
- No more than four festival cards render at once.
- Non-recommendation pages are unchanged.
- The relevant focused tests and the existing test suite pass.
