import asyncio
import logging

logger = logging.getLogger(__name__)

async def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """
    Run a system command asynchronously.
    Returns (returncode, stdout, stderr)
    """
    try:
        if cmd[0] == "sudo" and "-n" not in cmd:
            cmd.insert(1, "-n")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        return (
            process.returncode or 0,
            stdout.decode('utf-8').strip(),
            stderr.decode('utf-8').strip()
        )
    except Exception as e:
        logger.error(f"Command execution failed: {cmd} - {str(e)}")
        return 1, "", str(e)
