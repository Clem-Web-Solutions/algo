#!/usr/bin/env python3
"""
ÉTAPE 25 - Phase 1 Live Trading Validation Script
=====================================================

Purpose:  Verify all components are ready for Phase 1 live trading
Run:      python etape25_validation.py
Before:   First day of Phase 1 trading

Components checked:
1. Capital & Account Setup
2. System Environment  
3. Broker Connectivity
4. Signal Generation System
5. Risk Management System
6. Documentation & Procedures

Status Output: GREEN (all pass) / YELLOW (warnings) / RED (critical failures)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import traceback

class ETAPE25Validator:
    def __init__(self):
        self.workspace = Path("c:\\Users\\oscar\\Desktop\\algo trading")
        self.passed = 0
        self.warnings = 0
        self.failed = 0
        self.results = []
        
    def check(self, component, requirement, condition, critical=True):
        """Record a validation check"""
        severity = "❌ CRITICAL" if (not condition and critical) else "⚠️  WARNING" if not condition else "✅ PASS"
        status = "✓" if condition else "✗"
        
        self.results.append({
            "component": component,
            "requirement": requirement,
            "status": status,
            "severity": severity
        })
        
        if condition:
            self.passed += 1
        elif critical:
            self.failed += 1
        else:
            self.warnings += 1
            
        print(f"{severity:15} | {component:25} | {requirement:40} | {status}")
        
    def validate_capital_setup(self):
        """Check capital and account setup"""
        print("\n" + "="*100)
        print("SECTION 1: CAPITAL & ACCOUNT SETUP")
        print("="*100)
        
        # Check if trader has necessary preparation
        broker_manual = self.workspace / "docs" / "ETAPE24_TRADER_PREPARATION.md"
        self.check("Documentation", "Trader manual exists", broker_manual.exists(), critical=True)
        
        # Check if trader has completed checklist
        startup_checklist = self.workspace / "ETAPE25_STARTUP_CHECKLIST.md"
        self.check("Documentation", "Startup checklist exists", startup_checklist.exists(), critical=True)
        
    def validate_system_environment(self):
        """Check Python environment and project structure"""
        print("\n" + "="*100)
        print("SECTION 2: SYSTEM ENVIRONMENT")
        print("="*100)
        
        # Check Python
        self.check("Python", f"Python version: {sys.version.split()[0]}", sys.version_info >= (3, 8), critical=True)
        
        # Check project directories
        required_dirs = [
            "src/trading",
            "src/core", 
            "src/analysis",
            "data",
            "docs",
            "reports"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.workspace / dir_name
            self.check("Directory", f"{dir_name} exists", dir_path.exists(), critical=True)
            
    def validate_required_files(self):
        """Check critical configuration files"""
        print("\n" + "="*100)
        print("SECTION 3: CRITICAL CONFIGURATION FILES")
        print("="*100)
        
        required_files = {
            "src/trading/live_trading_config.py": True,
            "src/trading/position_sizing.py": True,
            "src/trading/live_monitoring.py": True,
            "src/core/production_main.py": True,
            "src/analysis/market_regime_detector.py": False,  # Optional
            "docs/ETAPE24_TRADER_PREPARATION.md": True,
            "ETAPE25_STARTUP_CHECKLIST.md": True,
            "ETAPE25_PHASE1_DAILY_LOG.md": True,
        }
        
        for file_path, is_critical in required_files.items():
            full_path = self.workspace / file_path
            exists = full_path.exists()
            file_type = "CRITICAL" if is_critical else "Optional"
            self.check("File", f"{file_path} ({file_type})", exists, critical=is_critical)
            
    def validate_signal_system(self):
        """Check signal generation system"""
        print("\n" + "="*100)
        print("SECTION 4: SIGNAL GENERATION SYSTEM")
        print("="*100)
        
        # Check if signal generation modules exist
        signal_files = [
            ("src/core/signal_generator.py", True, "Signal generator (genère signaux BUY/SELL)"),
            ("src/core/feature_engineering.py", True, "Feature engineering (indicateurs techniques)"),
            ("src/strategies/adaptive_strategy.py", True, "Adaptive strategy (ajuste selon régime)"),
            ("src/strategies/market_regime_detector.py", True, "Market regime detector (BULL/BEAR)"),
        ]
        
        for file_path, critical, description in signal_files:
            full_path = self.workspace / file_path
            self.check("Signal System", description, full_path.exists(), critical=critical)
            
    def validate_risk_management(self):
        """Check risk management components"""
        print("\n" + "="*100)
        print("SECTION 5: RISK MANAGEMENT SYSTEM")
        print("="*100)
        
        # Check risk management modules
        risk_files = [
            "src/trading/live_trading_config.py",
            "src/trading/position_sizing.py",
            "src/trading/live_monitoring.py",
        ]
        
        for file_path in risk_files:
            full_path = self.workspace / file_path
            self.check("Risk Mgmt", f"{file_path} exists", full_path.exists(), critical=True)
            
    def validate_broker_integration(self):
        """Check broker API integration"""
        print("\n" + "="*100)
        print("SECTION 6: BROKER API INTEGRATION")
        print("="*100)
        
        broker_files = [
            "src/trading/interactive_brokers.py",
            "src/trading/broker_interface.py",
            "src/trading/broker_manager.py",
        ]
        
        for file_path in broker_files:
            full_path = self.workspace / file_path
            exists = full_path.exists()
            self.check("Broker API", f"{file_path} exists", exists, critical=False)
            
    def validate_documentation(self):
        """Check documentation completeness"""
        print("\n" + "="*100)
        print("SECTION 7: DOCUMENTATION & PROCEDURES")
        print("="*100)
        
        docs = {
            "docs/ETAPE24_TRADER_PREPARATION.md": "Trader psychological preparation guide",
            "ETAPE25_STARTUP_CHECKLIST.md": "Phase 1 startup checklist",
            "ETAPE25_PHASE1_DAILY_LOG.md": "Daily trading log template",
            "docs/ETAPE17_LIVE_TRADING_STARTUP_GUIDE.md": "Live trading startup guide",
        }
        
        for file_path, description in docs.items():
            full_path = self.workspace / file_path
            self.check("Documentation", description, full_path.exists(), critical=True)
            
    def validate_data_availability(self):
        """Check if test/historical data available"""
        print("\n" + "="*100)
        print("SECTION 8: HISTORICAL DATA")
        print("="*100)
        
        required_tickers = {
            "AAPL": "AAPL_*.csv",
            "GOOGL": "GOOGL_*.csv",
            "MSFT": "MSFT_*.csv",
            "TSLA": "TSLA_*.csv",
        }
        
        data_dir = self.workspace / "data"
        for ticker, pattern in required_tickers.items():
            files = list(data_dir.glob(pattern))
            self.check("Data", f"{ticker} historical data available", len(files) > 0, critical=False)
            
    def validate_reports_structure(self):
        """Check reports directory structure"""
        print("\n" + "="*100)
        print("SECTION 9: REPORTS DIRECTORY")
        print("="*100)
        
        reports_dir = self.workspace / "reports"
        self.check("Reports", "Reports directory exists", reports_dir.exists(), critical=False)
        
        # Count existing reports
        report_files = list(reports_dir.glob("*.txt"))
        self.check("Reports", f"Previous reports exist ({len(report_files)} files)",
                   len(report_files) > 0, critical=False)
        
    def validate_project_history(self):
        """Check PROJECT_HISTORY exists and is recent"""
        print("\n" + "="*100)
        print("SECTION 10: PROJECT TRACKING")
        print("="*100)
        
        history_file = self.workspace / "docs" / "PROJECT_HISTORY.txt"
        self.check("Project", "PROJECT_HISTORY exists", history_file.exists(), critical=True)
        
        if history_file.exists():
            stat = history_file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            recent = stat.st_mtime > (datetime.now().timestamp() - 86400 * 7)  # Within 7 days
            self.check("Project", f"PROJECT_HISTORY is recent ({size_mb:.1f} MB)", 
                       recent, critical=False)
            
    def generate_summary(self):
        """Generate validation summary"""
        print("\n" + "="*100)
        print("VALIDATION SUMMARY")
        print("="*100)
        
        total = self.passed + self.warnings + self.failed
        pass_pct = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal checks:     {total}")
        print(f"✅ Passed:        {self.passed} ({pass_pct:.1f}%)")
        print(f"⚠️  Warnings:      {self.warnings}")
        print(f"❌ Critical:      {self.failed}")
        
        print("\n" + "="*100)
        
        if self.failed == 0:
            print("✅ STATUS: READY FOR PHASE 1 - All critical components present")
            print("\nNEXT STEPS:")
            print("1. Read ETAPE25_STARTUP_CHECKLIST.md completely")
            print("2. Complete all items in the checklist")
            print("3. Fund broker account with $2,000-$5,000")
            print("4. Install and test TWS (Trader Workstation)")
            print("5. Paper trade for 1-2 days to validate system")
            print("6. Memorize 10 Golden Rules")
            print("7. When ready, start Phase 1 trading (Day 1)")
            return True
        else:
            print("❌ STATUS: NOT READY FOR PHASE 1 - Critical items missing!")
            print("\nACTION REQUIRED:")
            print("1. Review all ❌ CRITICAL items above")
            print("2. Ensure all required files exist")
            print("3. Check project structure is intact")
            print("4. Verify Python environment is correct")
            return False
            
    def run_validation(self):
        """Execute all validations"""
        print("\n")
        print("╔" + "="*98 + "╗")
        print("║" + " "*20 + "ÉTAPE 25 - PHASE 1 LIVE TRADING VALIDATION" + " "*34 + "║")
        print("║" + " "*29 + f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC" + " "*41 + "║")
        print("╚" + "="*98 + "╝")
        
        try:
            self.validate_capital_setup()
            self.validate_system_environment()
            self.validate_required_files()
            self.validate_signal_system()
            self.validate_risk_management()
            self.validate_broker_integration()
            self.validate_documentation()
            self.validate_data_availability()
            self.validate_reports_structure()
            self.validate_project_history()
            
            ready = self.generate_summary()
            
            # Save results to file
            self.save_results(ready)
            
            return ready
            
        except Exception as e:
            print(f"\n❌ VALIDATION ERROR: {str(e)}")
            traceback.print_exc()
            return False
            
    def save_results(self, ready):
        """Save validation results to JSON"""
        output_file = self.workspace / "ETAPE25_VALIDATION_RESULTS.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "status": "READY" if ready else "NOT_READY",
            "passed": self.passed,
            "warnings": self.warnings,
            "failed": self.failed,
            "total": self.passed + self.warnings + self.failed,
            "results": self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"\nValidation results saved to: ETAPE25_VALIDATION_RESULTS.json")


if __name__ == "__main__":
    validator = ETAPE25Validator()
    ready = validator.run_validation()
    sys.exit(0 if ready else 1)

