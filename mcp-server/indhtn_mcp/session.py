"""Session management for InductorHTN REPL processes"""

import asyncio
import signal
import uuid
from asyncio.subprocess import Process
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class IndHTNSession:
    """Manages a single InductorHTN REPL session"""
    
    def __init__(self, session_id: str, files: List[str]):
        self.session_id = session_id
        self.files = files
        self.process: Optional[Process] = None
        self.trace_enabled = False
        self.last_query = ""
        self.output_buffer = ""
        self.ready_event = asyncio.Event()
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        
    async def start(self, indhtn_path: str, working_dir: Optional[str] = None):
        """Start the REPL subprocess"""
        cmd = [indhtn_path] + self.files
        
        logger.info(f"Starting InductorHTN session {self.session_id} with command: {' '.join(cmd)}")
        
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=working_dir,
            bufsize=0  # Unbuffered for real-time interaction
        )
        
        # Start output reader task
        self._reader_task = asyncio.create_task(self._read_output())
        
        # Give the process a moment to start
        await asyncio.sleep(0.5)
        
        # Wait for initial prompt
        await self._wait_for_prompt(timeout=10.0)
        
    async def _read_output(self):
        """Continuously read output from the process"""
        while self.process and self.process.returncode is None:
            try:
                # Read character by character to catch prompts
                char = await self.process.stdout.read(1)
                if not char:
                    break
                    
                char_str = char.decode('utf-8', errors='replace')
                self.output_buffer += char_str
                
                # Check if we've completed a prompt
                if self.output_buffer.endswith('?- '):
                    self.ready_event.set()
                    
            except Exception as e:
                logger.error(f"Error reading output from session {self.session_id}: {e}")
                break
    
    async def _wait_for_prompt(self, timeout: float = 3.0):
        """Wait for the REPL to be ready for input"""
        self.ready_event.clear()
        # Don't clear the buffer here - it might already contain output
        
        try:
            await asyncio.wait_for(self.ready_event.wait(), timeout)
        except asyncio.TimeoutError:
            # Check if we have a prompt in the buffer even if event wasn't set
            if '?-' in self.output_buffer:
                # Found prompt in buffer, continue
                pass
            else:
                raise TimeoutError(f"REPL did not become ready within {timeout}s")
            
        # Extract everything before the prompt
        output = self._extract_output()
        return output
        
    def _extract_output(self) -> str:
        """Extract output up to the prompt"""
        # Find the last occurrence of '?-'
        prompt_idx = self.output_buffer.rfind('?-')
        if prompt_idx != -1:
            result = self.output_buffer[:prompt_idx].strip()
            # Keep the prompt in buffer for next time
            self.output_buffer = self.output_buffer[prompt_idx:]
            return result
        return self.output_buffer.strip()
    
    async def send_query(self, query: str, timeout: float = 10.0) -> str:
        """Send a query and get the response"""
        if not self.process:
            raise RuntimeError("Session not started")
            
        self.last_accessed = datetime.now()
        
        # Commands starting with / don't need a period
        if not query.strip().startswith('/'):
            # Ensure query ends with period for Prolog queries
            if not query.strip().endswith('.'):
                query = query.strip() + '.'
                
        self.last_query = query
        
        logger.debug(f"Session {self.session_id} sending query: {query}")
        
        # Send query
        self.process.stdin.write((query + '\n').encode('utf-8'))
        await self.process.stdin.drain()
        
        # Wait for response
        output = await self._wait_for_prompt(timeout)
        
        logger.debug(f"Session {self.session_id} received output: {output[:200]}...")
        
        return output
    
    async def terminate(self):
        """Terminate the session"""
        if self.process and self.process.returncode is None:
            logger.info(f"Terminating session {self.session_id}")
            self.process.terminate()
            await self.process.wait()
        
        if hasattr(self, '_reader_task'):
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass


class SessionManager:
    """Manages multiple InductorHTN REPL sessions"""
    
    def __init__(self, indhtn_path: str, max_sessions: int = 10):
        self.indhtn_path = indhtn_path
        self.sessions: Dict[str, IndHTNSession] = {}
        self.max_sessions = max_sessions
        
    async def create_session(self, files: List[str], working_dir: Optional[str] = None) -> Tuple[str, str]:
        """Create a new REPL session"""
        if len(self.sessions) >= self.max_sessions:
            # Clean up oldest inactive session
            await self._cleanup_oldest_session()
            
        session_id = str(uuid.uuid4())
        session = IndHTNSession(session_id, files)
        
        try:
            await session.start(self.indhtn_path, working_dir)
            
            # Extract compilation results from initial output
            compilation_output = session._extract_output()
            
            self.sessions[session_id] = session
            return session_id, compilation_output
        except Exception as e:
            # Clean up on failure
            if session.process:
                session.process.terminate()
            raise RuntimeError(f"Failed to start session: {e}")
    
    async def execute_query(self, session_id: str, query: str, timeout: float = 10.0) -> Dict:
        """Execute a query in a session with comprehensive error handling"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        try:
            # Check if process is still alive
            if session.process.returncode is not None:
                raise RuntimeError("REPL process has terminated")
                
            result = await session.send_query(query, timeout)
            
            # Parse for known error patterns
            if "Error:" in result:
                return {
                    "success": False,
                    "output": result,
                    "error_type": self._classify_error(result)
                }
            
            return {
                "success": True,
                "output": result
            }
            
        except asyncio.TimeoutError:
            # Attempt recovery
            await self._attempt_recovery(session)
            return {
                "success": False,
                "output": "",
                "error_type": "timeout",
                "message": f"Query timed out after {timeout}s"
            }
        except Exception as e:
            logger.error(f"Error executing query in session {session_id}: {e}")
            return {
                "success": False,
                "output": "",
                "error_type": "runtime",
                "message": str(e)
            }

    async def get_state_diff(self, session_id: str, goal: str, timeout: float = 30.0) -> Dict:
        """
        Preview what plan would be generated for a goal without applying it.
        Does NOT apply the changes - just shows the plan that would be executed.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Find plans without applying
        goal_query = f"goals({goal})." if not goal.startswith("goals(") else goal
        plan_result = await self.execute_query(session_id, goal_query, timeout)

        if not plan_result.get("success"):
            return {
                "success": False,
                "error": plan_result.get("output", "Planning failed"),
                "error_type": plan_result.get("error_type", "unknown")
            }

        return {
            "success": True,
            "goal": goal,
            "plan": plan_result.get("output", ""),
            "note": "Use indhtn_apply_plan to actually apply changes and see final state"
        }

    async def step_operator(self, session_id: str, operator: str, timeout: float = 10.0) -> Dict:
        """
        Execute a single operator using apply() and return new state.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Use apply() to execute the single operator
        apply_query = f"apply({operator})."
        result = await self.execute_query(session_id, apply_query, timeout)

        if not result.get("success"):
            return {
                "success": False,
                "operator": operator,
                "error": result.get("output", "Operator execution failed"),
                "error_type": result.get("error_type", "unknown")
            }

        return {
            "success": True,
            "operator": operator,
            "result": result.get("output", ""),
            "message": "Operator applied. Query facts to see new state."
        }

    def _classify_error(self, error_text: str) -> str:
        """Classify error types for better handling"""
        if "Expected query" in error_text:
            return "syntax_error"
        elif "Out of memory" in error_text:
            return "memory_error"
        elif "Undefined" in error_text:
            return "undefined_predicate"
        else:
            return "unknown_error"
    
    async def _attempt_recovery(self, session: IndHTNSession):
        """Try to recover a stuck session"""
        logger.warning(f"Attempting recovery for session {session.session_id}")
        
        try:
            # Send interrupt signal
            session.process.send_signal(signal.SIGINT)
            await asyncio.sleep(0.5)
            
            # Check if still responsive
            test_output = await session.send_query("true.", timeout=2.0)
            if "yes" in test_output.lower():
                logger.info(f"Recovery successful for session {session.session_id}")
                return  # Recovery successful
        except:
            pass
            
        # If recovery failed, terminate and restart
        logger.warning(f"Recovery failed for session {session.session_id}, restarting")
        await session.terminate()
        await session.start(self.indhtn_path)
    
    async def _cleanup_oldest_session(self):
        """Remove the oldest session to make room"""
        if not self.sessions:
            return
            
        oldest_id = min(
            self.sessions.keys(),
            key=lambda sid: self.sessions[sid].last_accessed
        )
        
        logger.info(f"Cleaning up oldest session {oldest_id}")
        await self.end_session(oldest_id)
    
    async def end_session(self, session_id: str):
        """End a specific session"""
        session = self.sessions.get(session_id)
        if session:
            await session.terminate()
            del self.sessions[session_id]
            logger.info(f"Ended session {session_id}")
    
    async def end_all_sessions(self):
        """End all active sessions"""
        for session_id in list(self.sessions.keys()):
            await self.end_session(session_id)