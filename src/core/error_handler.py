"""
Error Handler et Logging - Etape 10
Gestion robuste des erreurs et logging systematique
Production-ready
"""
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


# ============================================================================
# SETUP LOGGING
# ============================================================================

def setup_logger(name, log_file=None, log_dir='reports', level=logging.INFO):
    """
    Setup logger robuste avec file et console
    
    Args:
        name: Nom du logger
        log_file: Nom fichier log (auto-generated si None)
        log_dir: Repertoire logs
        level: Niveau logging
    
    Returns:
        Logger objet
    """
    # Creer dossier logs
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True, parents=True)
    
    # Auto-generate log file name
    if log_file is None:
        log_file = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    log_filepath = log_path / log_file
    
    # Creer formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Eviter d'accumuler les handlers a chaque re-initialisation (cause spam logs)
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger, str(log_filepath)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class TradingException(Exception):
    """Base exception pour le systeme trading"""
    pass


class DataFetchException(TradingException):
    """Erreur telechargement donnees"""
    pass


class FeatureEngineeringException(TradingException):
    """Erreur creation features"""
    pass


class ModelException(TradingException):
    """Erreur entrainement/prediction modele"""
    pass


class BacktestException(TradingException):
    """Erreur backtesting"""
    pass


class ConfigException(TradingException):
    """Erreur configuration"""
    pass


# ============================================================================
# ERROR HANDLER
# ============================================================================

class ErrorHandler:
    """Gestionnaire central d'erreurs avec recovery"""
    
    def __init__(self, logger=None):
        """
        Init error handler
        
        Args:
            logger: Logger objet (cree nouveau si None)
        """
        self.logger = logger or logging.getLogger('ErrorHandler')
        self.error_count = 0
        self.warning_count = 0
        self.last_error = None
    
    def handle_error(self, exception, context="", critical=False):
        """
        Gere une erreur
        
        Args:
            exception: Exception a gerer
            context: Contexte de l'erreur
            critical: Si True, log comme erreur critique et re-raise
        
        Returns:
            True si recuperable, False sinon
        """
        self.error_count += 1
        self.last_error = {
            'exception': exception,
            'context': context,
            'timestamp': datetime.now(),
            'traceback': traceback.format_exc()
        }
        
        error_msg = f"[ERROR-{self.error_count}] {context}: {str(exception)}"
        
        if critical:
            self.logger.critical(error_msg)
            self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            raise exception
        else:
            self.logger.warning(error_msg)
            self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            
        return True
    
    def handle_warning(self, message, context=""):
        """
        Log une warning
        
        Args:
            message: Message warning
            context: Contexte
        """
        self.warning_count += 1
        warning_msg = f"[WARNING-{self.warning_count}] {context}: {message}"
        self.logger.warning(warning_msg)
    
    def validate_data(self, data, min_rows=100, required_columns=None):
        """
        Valide les donnees
        
        Args:
            data: DataFrame donnees
            min_rows: Nombre minimum de rows requis
            required_columns: Colonnes requises
        
        Returns:
            (True, None) si valide, (False, error_msg) sinon
        """
        try:
            if data is None or len(data) == 0:
                return False, "Donnees vides"
            
            if len(data) < min_rows:
                return False, f"Donnees insuffisantes: {len(data)} rows < {min_rows}"
            
            if required_columns:
                missing = [col for col in required_columns if col not in data.columns]
                if missing:
                    return False, f"Colonnes manquantes: {missing}"
            
            if data.isnull().sum().sum() > len(data) * 0.5:  # > 50% NaN
                return False, "Trop de valeurs manquantes (>50%)"
            
            return True, None
        
        except Exception as e:
            return False, f"Erreur validation: {str(e)}"
    
    def validate_config(self, config_dict, required_keys):
        """
        Valide configuration
        
        Args:
            config_dict: Dict configuration
            required_keys: Cles requises
        
        Returns:
            (True, None) si valide, (False, error_msg) sinon
        """
        try:
            if not isinstance(config_dict, dict):
                return False, "Configuration doit etre un dict"
            
            missing = [k for k in required_keys if k not in config_dict]
            if missing:
                return False, f"Cles manquantes: {missing}"
            
            return True, None
        
        except Exception as e:
            return False, f"Erreur validation config: {str(e)}"
    
    @contextmanager
    def error_context(self, context_name, critical=False):
        """
        Context manager pour gestion erreurs
        
        Usage:
            with handler.error_context("Telecharger donnees"):
                # code can fail here
        """
        try:
            self.logger.info(f"[START] {context_name}")
            yield self
            self.logger.info(f"[OK] {context_name}")
        
        except Exception as e:
            if critical:
                self.handle_error(e, context_name, critical=True)
            else:
                self.handle_error(e, context_name, critical=False)
                self.logger.error(f"[FAILED] {context_name}")


# ============================================================================
# SYSTEM HEALTH CHECK
# ============================================================================

class SystemHealthCheck:
    """Verifie la sante du systeme"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger('SystemHealth')
        self.checks = {}
    
    def check_disk_space(self, min_gb=5):
        """Verifie espace disque"""
        try:
            import shutil
            stat = shutil.disk_usage('/')
            free_gb = stat.free / (1024**3)
            
            if free_gb < min_gb:
                self.checks['disk_space'] = f"CRITICAL: {free_gb:.1f}GB < {min_gb}GB"
                return False
            else:
                self.checks['disk_space'] = f"OK: {free_gb:.1f}GB available"
                return True
        except Exception as e:
            self.checks['disk_space'] = f"ERROR: {str(e)}"
            return False
    
    def check_memory(self, max_pct=90):
        """Verifie utilisation memoire"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            if memory.percent > max_pct:
                self.checks['memory'] = f"CRITICAL: {memory.percent:.1f}% used > {max_pct}%"
                return False
            else:
                self.checks['memory'] = f"OK: {memory.percent:.1f}% used"
                return True
        except:
            # psutil pas dispo - return OK
            self.checks['memory'] = "UNKNOWN (psutil not available)"
            return True
    
    def check_directories(self, dirs):
        """Verifie existence dossiers"""
        try:
            missing = [d for d in dirs if not Path(d).exists()]
            
            if missing:
                self.checks['directories'] = f"MISSING: {missing}"
                return False
            else:
                self.checks['directories'] = f"OK: All directories exist"
                return True
        except Exception as e:
            self.checks['directories'] = f"ERROR: {str(e)}"
            return False
    
    def get_health_report(self):
        """Retourne rapport sante systeme"""
        report = "SYSTEM HEALTH CHECK\n"
        report += "=" * 50 + "\n"
        for check, result in self.checks.items():
            status = "[OK]" if "OK:" in result else "[ERROR]" if "ERROR:" in result else "[CRITICAL]"
            report += f"{status} {check}: {result}\n"
        return report


# ============================================================================
# DECORATOR POUR ERROR HANDLING
# ============================================================================

def safe_execution(function_name="unnamed", logger=None):
    """
    Decorator pour executer fonction avec error handling
    
    Usage:
        @safe_execution("Mon fonction")
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            try:
                log.info(f"[START] {function_name}")
                result = func(*args, **kwargs)
                log.info(f"[OK] {function_name}")
                return result
            except Exception as e:
                log.error(f"[FAILED] {function_name}: {str(e)}")
                log.debug(traceback.format_exc())
                raise
        return wrapper
    return decorator


if __name__ == '__main__':
    # Test
    logger, log_file = setup_logger('test')
    logger.info("Logger test OK")
    
    handler = ErrorHandler(logger)
    handler.handle_warning("Test warning", "Testing")
    
    health = SystemHealthCheck(logger)
    health.check_disk_space()
    health.check_memory()
    health.check_directories(['.', 'data', 'reports'])
    
    print("\n" + health.get_health_report())
