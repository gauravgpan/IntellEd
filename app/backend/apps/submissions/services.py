"""
Extraction worker stub (design doc section 8: upload -> OCR/vision extract
-> review -> confirm). No real OCR/vision model is wired up yet — this is
the seam where one plugs in. Called synchronously for now; swap for a queued
task (Celery, RQ, etc.) once there's an actual worker to run async.
"""

import logging

from django.utils import timezone

from .models import Submission

logger = logging.getLogger("thinkturf.extraction")


def run_extraction(submission: Submission):
    """
    Marks a submission NeedsReview with no extracted entries yet.
    Replace the body with a real call to an OCR/vision pipeline that reads
    submission.image_ref and creates SubmissionEntry rows with
    extracted_value + confidence per item.
    """
    submission.status = Submission.STATUS_PROCESSING
    submission.save(update_fields=["status"])

    logger.info("Extraction stub ran for submission %s — no model wired up yet", submission.id)

    submission.status = Submission.STATUS_NEEDS_REVIEW
    submission.save(update_fields=["status"])
    return submission
