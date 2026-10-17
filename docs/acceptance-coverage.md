# Acceptance coverage for v1

Each scenario of `docs/spec.md` section 8 and the test that covers it, as `DECISIONS.md` D-027
asks before the `v0.1.0` tag. `B` is `backend/tests/` (written by the agent), `A` is
`tests/acceptance/` (Diogo's). Checked on 2026-10-17 against `main` at `6f55342`, by reading
each test against the scenario title and the spec rule behind it, not only the test name.

To list the tests of one scenario: `pytest --collect-only -q -k "test_12_"`.

## Scheduling and caps (spec 4.6, 4.7)

| # | Scenario | Test | Note |
| --- | --- | --- | --- |
| 1 | Again, Hard or Good update the card through Py-FSRS and save a log | B `test_review_scheduling.py::test_1_rating_updates_the_card_through_py_fsrs_and_saves_a_review_log` | |
| 2 | There is no Easy rating | B `test_review_scheduling.py::test_2_there_is_no_easy_rating` | |
| 3 | 30 due, cap 20: the queue has 20 | B `test_review_scheduling.py::test_3_with_30_cards_due_and_a_cap_of_20_the_queue_has_20` | |
| 4 | The 20 picked have the lowest retrievability | B `test_review_scheduling.py::test_4_the_cards_picked_have_the_lowest_retrievability` | |
| 5 | Cards left out stay due, due date unchanged | B `test_review_scheduling.py::test_5_cards_left_out_stay_due_with_their_due_date_unchanged` | |
| 6 | 8 new cards, new card cap 5: 5 introduced | B `test_review_scheduling.py::test_6_with_8_new_cards_and_a_cap_of_5_the_queue_introduces_5` | |
| 7 | Pending, suspended and rejected never enter the queue | B `test_review_scheduling.py::test_7_pending_suspended_and_rejected_cards_never_enter_the_queue` | |
| 8 | "Reviews today" within the remaining cap, no overdue counts | B `test_review_scheduling.py::test_8_reviews_today_never_exceeds_the_remaining_cap`, `test_8_the_api_shows_only_the_capped_count_never_overdue_totals` | The second test is new in this PR: the "no overdue counts" half had no test. |
| 9 | Changing the review cap changes today's remaining count | B `test_review_scheduling.py::test_9_changing_the_review_cap_changes_todays_remaining_count` | |
| 10 | A review at 22:30 in Bahia counts toward that Bahia day | B `test_review_scheduling.py::test_10_a_review_at_22_30_in_bahia_counts_toward_that_bahia_day` | |
| 11 | A card failed and shown again uses no other slot | B `test_review_scheduling.py::test_11_a_card_failed_and_shown_again_the_same_day_uses_no_other_slot` | |
| 12 | Last session Monday, Friday opens a return session of at most 5 | B `test_home.py::test_12_last_session_on_monday_opening_on_friday_starts_a_return_session` | Through the API too: `test_the_review_screen_gets_at_most_5_cards_in_a_return_session`. |
| 13 | Last session Monday, Thursday is not a return session | B `test_home.py::test_13_last_session_on_monday_opening_on_thursday_is_not_a_return_session` | |
| 14 | Return session reviews count toward the day's cap | B `test_home.py::test_14_reviews_done_in_the_return_session_count_toward_that_days_cap` | When it ends: `test_14_another_activity_completed_today_ends_the_return_session` (D-026). |
| 15 | An abandoned activity does not count as a session | B `test_study_reading.py::test_15_an_abandoned_activity_does_not_count_as_a_session`, `test_home.py::test_15_an_abandoned_activity_does_not_end_the_absence` | |

## Status and completion (spec 4.2.2, 4.4)

| # | Scenario | Test | Note |
| --- | --- | --- | --- |
| 16 | No "Ideia central": draft | A `test_markdown_import.py::test_16_content_without_ideia_central_is_draft` | Saved state: A `test_card_approval.py::test_46_saving_without_ideia_central_keeps_the_content_as_draft`. |
| 17 | Only question without a reference answer: draft | A `test_markdown_import.py::test_17_content_whose_only_question_has_no_reference_answer_is_draft` | Parser level; the save stores the parsed state as is (`import_content`). |
| 18 | "Ideia central" and an answered question: ready | A `test_markdown_import.py::test_18_content_with_ideia_central_and_answered_question_is_ready` | Saved state: A `test_card_approval.py::test_46_saving_keeps_the_raw_markdown_the_blocks_in_order_and_the_state`. |
| 19 | Opening the first block moves to in progress | B `test_study_reading.py::test_19_opening_the_first_block_moves_the_subtopic_to_in_progress` | |
| 20 | Level, difficulty, status and review need change independently | B `test_completion_rules.py::test_20_the_four_classification_fields_change_independently` | |
| 21 | All blocks read and one partial attempt: suggested | B `test_completion_rules.py::test_21_all_blocks_read_and_one_partial_attempt_is_suggested_complete` | |
| 22 | All blocks read and only wrong attempts: not suggested | B `test_completion_rules.py::test_22_all_blocks_read_and_only_wrong_attempts_is_not_suggested` | |
| 23 | A suggestion changes the status only when Diogo confirms | B `test_completion_rules.py::test_23_a_suggestion_changes_the_status_only_when_diogo_confirms` | |
| 24 | Concept completed when all subtopics are, in progress when some are | B `test_completion_rules.py::test_24_a_concept_is_completed_when_all_subtopics_are_and_in_progress_when_some_are` | |
| 25 | Completing a concept keeps its cards in review | B `test_review_scheduling.py::test_25_completing_a_concept_keeps_its_cards_in_review` | Sets the status directly instead of confirming; the queue never reads the status, so the result is the same. |

## Markdown import (spec 4.2, 4.3)

| # | Scenario | Test | Note |
| --- | --- | --- | --- |
| 26 | Each known `##` heading is its own block, in order | A `test_markdown_import.py::test_26_each_known_heading_becomes_its_own_block_in_order` | |
| 27 | An unknown `##` heading is an extra block in place | A `test_markdown_import.py::test_27_unknown_heading_becomes_extra_block_in_its_original_position` | |
| 28 | `P1` with its reference answer is a question | A `test_markdown_import.py::test_28_p1_with_reference_answer_becomes_a_question` | |
| 29 | `C1: front :: back` is a pending card | A `test_markdown_import.py::test_29_c1_front_and_back_becomes_a_pending_card` | |
| 30 | Changed text under `P1` keeps its attempts | A `test_markdown_reimport.py::test_30_reimport_with_changed_text_under_p1_keeps_the_attempts_of_p1` | |
| 31 | Changed text under `C1` keeps its review history | A `test_markdown_reimport.py::test_31_reimport_with_changed_text_under_c1_keeps_the_review_history_of_c1` | |
| 32 | Without `P2`: archived, attempts kept | A `test_markdown_reimport.py::test_32_reimport_without_p2_archives_p2_and_keeps_its_attempts` | |
| 33 | Without `C2`: suspended | A `test_markdown_reimport.py::test_33_reimport_without_c2_suspends_c2` | |
| 34 | `C2` back is restored with its history | A `test_markdown_reimport.py::test_34_c2_back_restores_it_with_its_review_history_in_the_state_it_had` | |
| 35 | A new `C3` enters as pending | A `test_markdown_reimport.py::test_35_new_c3_on_reimport_enters_as_pending` | |
| 36 | Two `C1` labels block the save | A `test_markdown_import.py::test_36_two_c1_labels_in_one_document_block_the_save`, `test_markdown_reimport.py::test_36_a_document_with_duplicate_labels_is_not_saved`; B `test_content_saving.py::test_36_two_c1_labels_block_the_save_with_a_message_naming_the_label` | The B test is new in this PR: it checks the save endpoint answers 400 naming the label. |
| 37 | `[!ia]` without a `Fonte:` URL is marked | A `test_markdown_import.py::test_37_ia_callout_without_a_fonte_url_is_marked_as_unsourced` | The "complemento sem fonte" text is UI, not tested. |
| 38 | `[!ia]` with a `Fonte:` URL is not marked | A `test_markdown_import.py::test_38_ia_callout_with_a_fonte_url_is_not_marked` | |
| 39 | Frontmatter naming another subtopic warns and saves into the edited one | A `test_markdown_import.py::test_39_frontmatter_naming_another_subtopic_shows_a_warning`; B `test_content_saving.py::test_39_frontmatter_naming_another_subtopic_warns_and_saves_into_the_edited_one` | The B test is new in this PR: the A test covers only the warning, as its docstring says. |
| 40 | Approving makes a card active and subject to the new card cap | A `test_card_approval.py::test_40_approving_a_pending_card_makes_it_active_and_new`; B `test_review_scheduling.py::test_40_an_approved_card_is_subject_to_the_new_card_cap` | A covers "active", B the cap. |
| 41 | No way to approve all pending cards at once | A `test_card_approval.py::test_41_approving_one_card_leaves_the_others_pending` | Checks one collection URL; the UI has no such button. |
| 42 | A rejected card stays rejected on the same re-import | A `test_card_approval.py::test_42_a_rejected_card_stays_rejected_when_the_same_markdown_is_imported_again` | |

## Outside section 8

Tests numbered 43 to 51 cover scenarios proposed in later slices (43 to 48 card approval and
saving, 49 and 50 reading, 51 the home screen), and the backup tests cover spec 4.10. They are
not part of the section 8 list, so this map leaves them out.
