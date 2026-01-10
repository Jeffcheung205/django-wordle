"""
Management command to compile .po files to .mo files using Python's polib.
This is a fallback for systems without gettext tools installed.
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Compile .po files to .mo files using Python (gettext-free)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--locale',
            '-l',
            action='append',
            dest='locales',
            help='Locale(s) to compile (e.g. zh, en). Default is all.',
        )

    def handle(self, *args, **options):
        try:
            import polib
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    'polib is not installed. Install it with: poetry add polib --group dev'
                )
            )
            return

        locale_dir = Path(settings.BASE_DIR) / 'base' / 'locale'
        
        if not locale_dir.exists():
            self.stdout.write(self.style.ERROR(f'Locale directory not found: {locale_dir}'))
            return

        locales = options.get('locales', None)
        if locales:
            locale_codes = locales
        else:
            locale_codes = [
                d.name for d in locale_dir.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
            ]

        compiled_count = 0

        for lang_code in locale_codes:
            lang_dir = locale_dir / lang_code / 'LC_MESSAGES'
            
            if not lang_dir.exists():
                continue

            # Compile app.po to app.mo
            po_files = ['app.po', 'django.po', 'djangojs.po', 'allauth.po']
            
            for po_filename in po_files:
                po_file = lang_dir / po_filename
                if not po_file.exists():
                    continue
                
                mo_filename = po_filename.replace('.po', '.mo')
                mo_file = lang_dir / mo_filename
                
                try:
                    po = polib.pofile(str(po_file))
                    po.save_as_mofile(str(mo_file))
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Compiled {lang_code}/LC_MESSAGES/{mo_filename}'
                        )
                    )
                    compiled_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Failed to compile {lang_code}/{po_filename}: {e}'
                        )
                    )

        if compiled_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully compiled {compiled_count} file(s)')
            )
        else:
            self.stdout.write(self.style.WARNING('No translation files were compiled'))
