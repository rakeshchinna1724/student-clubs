import os

from django.core.exceptions import ValidationError


MAX_SHARED_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_SHARED_ATTACHMENT_SIZE_MB = MAX_SHARED_ATTACHMENT_SIZE // (1024 * 1024)
ALLOWED_SHARED_ATTACHMENT_EXTENSIONS = {
    '.csv',
    '.doc',
    '.docx',
    '.gif',
    '.jpeg',
    '.jpg',
    '.pdf',
    '.png',
    '.ppt',
    '.pptx',
    '.txt',
    '.webp',
    '.xls',
    '.xlsx',
    '.zip',
}


def validate_shared_attachment(file):
    extension = os.path.splitext(file.name)[1].lower()
    if extension not in ALLOWED_SHARED_ATTACHMENT_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_SHARED_ATTACHMENT_EXTENSIONS))
        raise ValidationError(f'Unsupported file type. Allowed types: {allowed}.')

    if file.size > MAX_SHARED_ATTACHMENT_SIZE:
        raise ValidationError(f'File size must be {MAX_SHARED_ATTACHMENT_SIZE_MB} MB or smaller.')
