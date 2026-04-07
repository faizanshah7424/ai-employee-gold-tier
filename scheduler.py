"""
Task Scheduler Integration - Silver Level Implementation
Provides scheduling via Windows Task Scheduler or cron

Per hackathon document Silver Tier:
"Basic scheduling via cron or Task Scheduler"

Usage:
    python scheduler.py install    # Install scheduled tasks
    python scheduler.py run        # Run scheduled task manually
    python scheduler.py status     # Check scheduled tasks
    python scheduler.py remove     # Remove scheduled tasks
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.absolute()
VAULT = PROJECT_DIR / "AI_Employee_Vault"


def create_scheduled_task_xml():
    """Create Windows Task Scheduler XML configuration"""
    
    python_exe = sys.executable
    orchestrator_script = PROJECT_DIR / "orchestrator.py"
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>AI Employee Orchestrator - Runs every 30 seconds</Description>
    <URI>\\AI_Employee_Orchestrator</URI>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT1M</Delay>
    </LogonTrigger>
    <CalendarTrigger>
      <StartBoundary>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
      <Repetition>
        <Interval>PT30S</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT72H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{python_exe}"</Command>
      <Arguments>"{orchestrator_script}"</Arguments>
      <WorkingDirectory>{PROJECT_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""
    
    xml_file = PROJECT_DIR / "ai_employee_task.xml"
    xml_file.write_text(xml_content, encoding="utf-8")
    return xml_file


def install_scheduled_task():
    """Install AI Employee as Windows Scheduled Task"""
    print("="*60)
    print("  Installing AI Employee Scheduled Task")
    print("="*60)
    
    xml_file = create_scheduled_task_xml()
    
    # Remove existing task if exists
    subprocess.run(
        ["schtasks", "/Delete", "/TN", "AI_Employee_Orchestrator", "/F"],
        capture_output=True
    )
    
    # Install new task
    result = subprocess.run(
        ["schtasks", "/Create", "/TN", "AI_Employee_Orchestrator", "/XML", str(xml_file), "/F"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n✓ Scheduled task installed successfully!")
        print("\nThe AI Employee orchestrator will now:")
        print("  - Start when you log in (1 minute delay)")
        print("  - Run every 30 seconds")
        print("  - Continue running in background")
        print("\nTo manage the task:")
        print("  - Open Task Scheduler")
        print("  - Find 'AI_Employee_Orchestrator' in task list")
        print("  - Right-click to Run/Disable/Delete")
    else:
        print(f"\n✗ Failed to install scheduled task")
        print(f"Error: {result.stderr}")
        print("\nManual installation:")
        print(f"  schtasks /Create /TN AI_Employee_Orchestrator /XML {xml_file} /F")
    
    return result.returncode == 0


def run_scheduled_task():
    """Run the scheduled task manually"""
    print("="*60)
    print("  Running AI Employee Orchestrator (Manual)")
    print("="*60)
    
    result = subprocess.run(
        ["schtasks", "/Run", "/TN", "AI_Employee_Orchestrator"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n✓ Orchestrator started!")
    else:
        print(f"\n✗ Failed to start orchestrator")
        print(f"Error: {result.stderr}")
    
    return result.returncode == 0


def check_task_status():
    """Check status of scheduled task"""
    print("="*60)
    print("  AI Employee Scheduled Task Status")
    print("="*60)
    
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", "AI_Employee_Orchestrator", "/V", "/FO", "LIST"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n" + result.stdout)
        
        # Also check if orchestrator is running
        orchestrator_running = False
        check_process = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe"],
            capture_output=True,
            text=True
        )
        
        if "orchestrator.py" in check_process.stdout.lower():
            orchestrator_running = True
        
        print(f"\nOrchestrator Process: {'Running' if orchestrator_running else 'Not Running'}")
    else:
        print("\n✗ Scheduled task not installed")
        print("\nTo install, run: python scheduler.py install")
    
    return result.returncode == 0


def remove_scheduled_task():
    """Remove the scheduled task"""
    print("="*60)
    print("  Removing AI Employee Scheduled Task")
    print("="*60)
    
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", "AI_Employee_Orchestrator", "/F"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n✓ Scheduled task removed successfully!")
    else:
        print(f"\n✗ Failed to remove scheduled task")
        print(f"Error: {result.stderr}")
    
    # Clean up XML file
    xml_file = PROJECT_DIR / "ai_employee_task.xml"
    if xml_file.exists():
        xml_file.unlink()
        print("✓ Configuration file removed")
    
    return result.returncode == 0


def create_cron_entry():
    """Create cron entry for Linux/Mac"""
    python_exe = sys.executable
    orchestrator_script = PROJECT_DIR / "orchestrator.py"
    
    # Cron entry to run every 30 seconds (using * /1 * * * * with sleep)
    cron_entry = f"""# AI Employee Orchestrator
# Runs every 30 seconds
* * * * * {python_exe} {orchestrator_script}
* * * * * sleep 30 && {python_exe} {orchestrator_script}
"""
    
    print("\nCron entry for Linux/Mac:")
    print(cron_entry)
    print("\nTo install:")
    print("  crontab -e")
    print("  # Paste the above lines")
    print("  # Save and exit")
    
    return cron_entry


def show_usage():
    """Show usage information"""
    print("""
AI Employee Task Scheduler - Silver Level
==========================================

Usage:
  python scheduler.py install    - Install as Windows Scheduled Task
  python scheduler.py run        - Run scheduled task manually
  python scheduler.py status     - Check task status
  python scheduler.py remove     - Remove scheduled task
  python scheduler.py cron       - Show cron entry for Linux/Mac
  python scheduler.py help       - Show this help message

Features:
  - Automatic startup on login
  - Runs every 30 seconds
  - Background execution
  - Easy management via Task Scheduler

Note: For Linux/Mac, use the 'cron' command to get cron entry.
""")


def main():
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "install":
        install_scheduled_task()
    elif command == "run":
        run_scheduled_task()
    elif command == "status":
        check_task_status()
    elif command == "remove":
        remove_scheduled_task()
    elif command == "cron":
        create_cron_entry()
    elif command == "help":
        show_usage()
    else:
        print(f"Unknown command: {command}")
        show_usage()


if __name__ == "__main__":
    main()
