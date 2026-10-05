"""
Extraction worker stub (design doc section 8: upload -> OCR/vision extract
-> review -> confirm). No real OCR/vision model is wired up yet — this is
the seam where one plugs in.

Runs as a Django-Q2 background task (queued via async_task in
apps/submissions/views.py), not inline in the request: a real OCR/vision
call is slow enough that running it synchronously would tie up an Apache
worker for the duration of every upload.
"""

import logging

from .models import Submission

logger = logging.getLogger("thinkturf.extraction")


def run_extraction(submission_id):
    """
    Marks a submission NeedsReview with no extracted entries yet.
    Replace the body with a real call to an OCR/vision pipeline that reads
    submission.image_ref and creates SubmissionEntry rows with
    extracted_value + confidence per item.

    Takes an id rather than a model instance: this runs in a separate
    worker process, so the row is re-fetched fresh rather than relying on
    a possibly-stale instance pickled at enqueue time.
    """
    submission = Submission.objects.get(pk=submission_id)

    submission.status = Submission.STATUS_PROCESSING
    submission.save(update_fields=["status"])

    logger.info("Extraction stub ran for submission %s — no model wired up yet", submission.id)

    submission.status = Submission.STATUS_NEEDS_REVIEW
    submission.save(update_fields=["status"])
    return str(submission.id)
