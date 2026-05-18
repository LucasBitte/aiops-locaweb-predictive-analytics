"""
Logger centralizado para Glue Job
Registra eventos em stdout e CloudWatch
"""

import logging
import sys
from datetime import datetime
from config import LOG_LEVEL, LOG_FORMAT


class GlueLogger:
    """Logger customizado para Glue Jobs."""

    def __init__(self, name="AIOps-Silver"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVEL)

        # Handler para stdout (CloudWatch)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.start_time = datetime.now()

    def info(self, msg):
        """Log de informação."""
        print(f"[INFO] {msg}")
        self.logger.info(msg)

    def error(self, msg):
        """Log de erro."""
        print(f"[ERROR] {msg}")
        self.logger.error(msg)

    def warning(self, msg):
        """Log de aviso."""
        print(f"[WARNING] {msg}")
        self.logger.warning(msg)

    def debug(self, msg):
        """Log de debug."""
        print(f"[DEBUG] {msg}")
        self.logger.debug(msg)

    def section(self, title):
        """Log de seção (com separadores)."""
        separator = "=" * 60
        msg = f"{separator}\n{title}\n{separator}"
        print(msg)
        self.logger.info(msg)

    def dataframe_info(self, name, df):
        """Log de informações do DataFrame."""
        msg = f"{name}: {df.count()} registros, {len(df.columns)} colunas"
        self.info(msg)

    def transition(self, from_state, to_state, record_count):
        """Log de transição entre estados."""
        delta = df_before - df_after if 'df_before' in locals() else 0
        msg = f"{from_state} → {to_state}: {record_count} registros"
        self.info(msg)

    def dict_stats(self, stats_dict, indent=2):
        """Log de dicionário de estatísticas."""
        import json
        stats_json = json.dumps(stats_dict, indent=indent, default=str)
        print(f"[STATS]\n{stats_json}")

    def elapsed_time(self):
        """Retorna tempo decorrido desde inicialização."""
        elapsed = datetime.now() - self.start_time
        return str(elapsed).split('.')[0]  # Remove microseconds

    def job_summary(self, total_input, total_output, duration):
        """Resumo final do job."""
        self.section("JOB SUMMARY")
        summary = {
            'status': 'SUCCESS',
            'input_records': total_input,
            'output_records': total_output,
            'records_filtered': total_input - total_output,
            'reduction_percent': f"{100 * (total_input - total_output) / total_input:.1f}%",
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.dict_stats(summary)
        return summary
