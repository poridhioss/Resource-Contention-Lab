import multiprocessing as mp
import math
import time
import os
import signal
import logging
from datetime import datetime
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CpuHogService:
    def __init__(self, cpu_cores=None, intensity="high"):
        self.cpu_cores = cpu_cores or mp.cpu_count()
        self.intensity = intensity
        self.processes = []
        self.start_time = time.time()
        self.should_stop = False
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info(f"Initializing CPU Hog Service:")
        logger.info(f"  - Target CPU cores: {self.cpu_cores}")
        logger.info(f"  - Intensity: {self.intensity}")
        logger.info(f"  - PID: {os.getpid()}")

    def signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True
        self.stop()

    def cpu_burn_worker(self, worker_id, intensity):
        """
        Worker function that burns CPU cycles
        """
        logger.info(f"Worker {worker_id} started with intensity {intensity}")
        
        # Set process name for easier identification
        try:
            import setproctitle
            setproctitle.setproctitle(f"cpu-hog-worker-{worker_id}")
        except ImportError:
            pass
        
        iteration_count = 0
        last_report = time.time()
        
        # Adjust computation intensity
        multiplier = {
            "low": 1000,
            "medium": 10000, 
            "high": 100000,
            "extreme": 1000000
        }.get(intensity, 10000)
        
        result = 0.0
        
        while True:
            # Perform CPU-intensive calculations
            for i in range(multiplier):
                result += math.sqrt(98765.4321 + i)
                result += math.sin(i * 0.001) * math.cos(i * 0.001)
                result += math.log(i + 1) * math.exp(-i * 0.0001)
                iteration_count += 1
            
            # Periodic reporting (every 10 seconds)
            if time.time() - last_report > 10:
                try:
                    process = psutil.Process()
                    cpu_percent = process.cpu_percent()
                    logger.info(f"Worker {worker_id}: {iteration_count} iterations, CPU: {cpu_percent:.1f}%")
                    last_report = time.time()
                except:
                    pass
            
            # Small yield to prevent complete system freeze (optional)
            if intensity == "medium":
                time.sleep(0.001)
            elif intensity == "low":
                time.sleep(0.01)

    def start_workers(self):
        """Start CPU burn workers"""
        logger.info(f"Starting {self.cpu_cores} CPU burn workers...")
        
        for i in range(self.cpu_cores):
            process = mp.Process(
                target=self.cpu_burn_worker,
                args=(i, self.intensity),
                name=f"cpu-hog-{i}"
            )
            process.start()
            self.processes.append(process)
            logger.info(f"Started worker {i} with PID {process.pid}")

    def monitor_system(self):
        """Monitor system resources and log periodically"""
        while not self.should_stop:
            try:
                # System-wide metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                load_avg = os.getloadavg()
                uptime = time.time() - self.start_time
                
                # Per-process metrics
                main_process = psutil.Process(os.getpid())
                main_cpu = main_process.cpu_percent()
                main_memory = main_process.memory_info().rss / 1024 / 1024
                
                logger.info(f"SYSTEM METRICS:")
                logger.info(f"  CPU Usage: {cpu_percent:.1f}%")
                logger.info(f"  Memory Usage: {memory.percent:.1f}%")
                logger.info(f"  Load Average: {', '.join([f'{l:.2f}' for l in load_avg])}")
                logger.info(f"  Uptime: {uptime:.0f}s")
                logger.info(f"  Main Process - CPU: {main_cpu:.1f}%, Memory: {main_memory:.1f}MB")
                logger.info(f"  Active Workers: {len([p for p in self.processes if p.is_alive()])}")
                
                time.sleep(30)  # Report every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(30)

    def stop(self):
        """Gracefully stop all workers"""
        logger.info("Stopping CPU Hog Service...")
        
        for i, process in enumerate(self.processes):
            if process.is_alive():
                logger.info(f"Terminating worker {i} (PID: {process.pid})")
                process.terminate()
        
        # Wait for processes to terminate
        for process in self.processes:
            process.join(timeout=5)
            if process.is_alive():
                logger.warning(f"Force killing worker {process.pid}")
                process.kill()
        
        logger.info("All workers stopped")

    def run(self):
        """Main run loop"""
        try:
            self.start_workers()
            self.monitor_system()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.stop()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CPU Hog Service for Contention Testing")
    parser.add_argument("--cores", type=int, default=None, 
                       help="Number of CPU cores to target (default: all)")
    parser.add_argument("--intensity", choices=["low", "medium", "high", "extreme"], 
                       default="high", help="CPU burn intensity")
    
    args = parser.parse_args()
    
    # Get actual CPU cores if not specified
    cores = args.cores or mp.cpu_count()
    
    logger.info(f"Starting CPU Hog Service with {cores} cores at {args.intensity} intensity")
    
    hog_service = CpuHogService(cpu_cores=cores, intensity=args.intensity)
    hog_service.run()