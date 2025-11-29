"""
Benchmark Email Reader Plugin - Test Performance Reali

Testa le performance del plugin con carichi di lavoro realistici
per verificare comportamento in produzione.
"""

import asyncio
import time
import statistics
import sys
from pathlib import Path

# Setup path
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from email_processor import EmailProcessor

class EmailBenchmark:
    """Benchmark performance email."""
    
    def __init__(self):
        self.processor = EmailProcessor()
        self.results = {}
    
    async def benchmark_email_list(self, provider_config, email_counts=[10, 25, 50, 100]):
        """Benchmark lista email con varie quantità."""
        print(f"🚀 Benchmark Lista Email - {provider_config['provider'].upper()}")
        print("-" * 50)
        
        results = {}
        
        for count in email_counts:
            print(f"\\n📊 Test con {count} email...")
            
            # Configura input
            test_config = provider_config.copy()
            test_config['max_emails'] = count
            test_config['include_body'] = True  # Test realistico
            
            times = []
            
            # Esegui 3 run per media
            for run in range(3):
                try:
                    start_time = time.time()
                    result = await self.processor.process(test_config)
                    end_time = time.time()
                    
                    if result['success']:
                        duration = end_time - start_time
                        times.append(duration)
                        email_count = result['email_count']
                        print(f"  Run {run+1}: {email_count} email in {duration:.2f}s")
                    else:
                        print(f"  Run {run+1}: ERRORE - {result['error']}")
                        break
                        
                except Exception as e:
                    print(f"  Run {run+1}: ECCEZIONE - {e}")
                    break
            
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                
                results[count] = {
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'emails_per_sec': count / avg_time,
                    'runs': len(times)
                }
                
                print(f"  📈 Media: {avg_time:.2f}s ({count/avg_time:.1f} email/s)")
                print(f"  ⚡ Range: {min_time:.2f}s - {max_time:.2f}s")
            else:
                results[count] = {'error': 'Tutti i run falliti'}
                print(f"  ❌ Test fallito per {count} email")
        
        return results
    
    async def benchmark_connection_overhead(self, provider_config, iterations=10):
        """Benchmark overhead connessione."""
        print(f"\\n🔌 Benchmark Overhead Connessione")
        print("-" * 40)
        
        connection_times = []
        
        for i in range(iterations):
            # Test con 1 email per misurare solo overhead connessione
            test_config = provider_config.copy()
            test_config['max_emails'] = 1
            test_config['include_body'] = False
            
            try:
                start_time = time.time()
                result = await self.processor.process(test_config)
                end_time = time.time()
                
                if result['success']:
                    duration = end_time - start_time
                    connection_times.append(duration)
                    print(f"  Connessione {i+1}: {duration:.3f}s")
                else:
                    print(f"  Connessione {i+1}: ERRORE")
                    
            except Exception as e:
                print(f"  Connessione {i+1}: ECCEZIONE - {e}")
        
        if connection_times:
            avg_connection = statistics.mean(connection_times)
            print(f"\\n📊 Overhead medio connessione: {avg_connection:.3f}s")
            return avg_connection
        else:
            print("\\n❌ Impossibile misurare overhead connessione")
            return None
    
    async def benchmark_body_vs_headers(self, provider_config):
        """Confronta performance con/senza corpo email."""
        print(f"\\n📝 Benchmark Corpo vs Headers")
        print("-" * 40)
        
        test_count = 25
        results = {}
        
        # Test solo headers
        print("\\n📄 Test solo headers...")
        test_config = provider_config.copy()
        test_config['max_emails'] = test_count
        test_config['include_body'] = False
        test_config['include_html'] = False
        
        try:
            start_time = time.time()
            result = await self.processor.process(test_config)
            headers_time = time.time() - start_time
            
            if result['success']:
                results['headers_only'] = {
                    'time': headers_time,
                    'emails': result['email_count'],
                    'speed': result['email_count'] / headers_time
                }
                print(f"  ✅ {result['email_count']} email in {headers_time:.2f}s")
            else:
                print(f"  ❌ Errore: {result['error']}")
                
        except Exception as e:
            print(f"  ❌ Eccezione: {e}")
        
        # Test con corpo
        print("\\n📝 Test con corpo...")
        test_config['include_body'] = True
        
        try:
            start_time = time.time()
            result = await self.processor.process(test_config)
            body_time = time.time() - start_time
            
            if result['success']:
                results['with_body'] = {
                    'time': body_time,
                    'emails': result['email_count'],
                    'speed': result['email_count'] / body_time
                }
                print(f"  ✅ {result['email_count']} email in {body_time:.2f}s")
                
                # Calcola overhead corpo
                if 'headers_only' in results:
                    overhead = body_time - headers_time
                    overhead_percent = (overhead / headers_time) * 100
                    print(f"\\n📊 Overhead corpo: +{overhead:.2f}s (+{overhead_percent:.1f}%)")
                    
            else:
                print(f"  ❌ Errore: {result['error']}")
                
        except Exception as e:
            print(f"  ❌ Eccezione: {e}")
        
        return results
    
    async def benchmark_filters_impact(self, provider_config):
        """Testa impatto filtri su performance."""
        print(f"\\n🔍 Benchmark Impatto Filtri")
        print("-" * 40)
        
        base_config = provider_config.copy()
        base_config['max_emails'] = 50
        base_config['include_body'] = False
        
        filter_tests = [
            {'name': 'Nessun filtro', 'filters': {}},
            {'name': 'Solo non lette', 'filters': {'unread_only': True}},
            {'name': 'Filtro data', 'filters': {'date_from': '2025-11-01'}},
            {'name': 'Filtro mittente', 'filters': {'sender_filter': 'test@example.com'}},
            {'name': 'Tutti i filtri', 'filters': {
                'unread_only': True,
                'date_from': '2025-11-01', 
                'sender_filter': 'notifications'
            }}
        ]
        
        results = {}
        
        for test in filter_tests:
            print(f"\\n🧪 {test['name']}...")
            
            test_config = base_config.copy()
            test_config.update(test['filters'])
            
            try:
                start_time = time.time()
                result = await self.processor.process(test_config)
                duration = time.time() - start_time
                
                if result['success']:
                    email_count = result['email_count']
                    results[test['name']] = {
                        'time': duration,
                        'emails': email_count,
                        'speed': email_count / duration if email_count > 0 else 0
                    }
                    print(f"  ✅ {email_count} email in {duration:.2f}s")
                else:
                    print(f"  ❌ Errore: {result['error']}")
                    results[test['name']] = {'error': result['error']}
                    
            except Exception as e:
                print(f"  ❌ Eccezione: {e}")
                results[test['name']] = {'error': str(e)}
        
        return results
    
    def print_benchmark_summary(self, all_results):
        """Stampa riepilogo completo benchmark."""
        print("\\n" + "=" * 60)
        print("📊 RIEPILOGO BENCHMARK COMPLETO")
        print("=" * 60)
        
        # Performance lista email
        if 'email_list' in all_results:
            print("\\n📧 Performance Lista Email:")
            for count, data in all_results['email_list'].items():
                if 'error' not in data:
                    print(f"  {count:3d} email: {data['emails_per_sec']:5.1f} email/s "
                          f"(avg: {data['avg_time']:.2f}s)")
        
        # Overhead connessione
        if 'connection_overhead' in all_results:
            overhead = all_results['connection_overhead']
            if overhead:
                print(f"\\n🔌 Overhead connessione: {overhead:.3f}s")
        
        # Corpo vs headers
        if 'body_comparison' in all_results:
            comp = all_results['body_comparison']
            if 'headers_only' in comp and 'with_body' in comp:
                headers_speed = comp['headers_only']['speed']
                body_speed = comp['with_body']['speed']
                print(f"\\n📝 Headers only: {headers_speed:.1f} email/s")
                print(f"📝 Con corpo:    {body_speed:.1f} email/s")
                print(f"📊 Ratio:        {headers_speed/body_speed:.1f}x più veloce senza corpo")
        
        # Raccomandazioni
        print("\\n💡 RACCOMANDAZIONI:")
        
        if 'email_list' in all_results:
            speeds = [data.get('emails_per_sec', 0) for data in all_results['email_list'].values() 
                     if 'error' not in data]
            if speeds:
                avg_speed = statistics.mean(speeds)
                if avg_speed > 20:
                    print("  ✅ Performance eccellenti per uso produzione")
                elif avg_speed > 10:
                    print("  ⚠️  Performance buone, monitora con carichi alti")
                else:
                    print("  ❌ Performance lente, ottimizza configurazione")
        
        # Consigli ottimizzazione
        print("\\n🔧 Ottimizzazioni suggerite:")
        print("  • Usa include_body=false se non serve il contenuto")
        print("  • Implementa cache per connessioni frequenti")
        print("  • Limita max_emails per API con rate limits")
        print("  • Usa filtri server-side per ridurre trasferimento dati")

async def run_full_benchmark():
    """Esegue benchmark completo."""
    print("⚡ BENCHMARK COMPLETO EMAIL READER PLUGIN")
    print("=" * 60)
    
    # Configurazione IMAP Gmail (più facile da testare)
    import os
    username = os.getenv('GMAIL_USERNAME')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not username or not password:
        print("❌ Configura variabili ambiente:")
        print("   set GMAIL_USERNAME=your-email@gmail.com")
        print("   set GMAIL_APP_PASSWORD=your-app-password")
        return False
    
    provider_config = {
        'operation': 'list',
        'provider': 'imap',
        'credentials_path': '/dummy',
        'imap_server': 'imap.gmail.com',
        'imap_port': 993,
        'username': username,
        'password': password
    }
    
    benchmark = EmailBenchmark()
    all_results = {}
    
    try:
        # Test lista email con varie quantità
        print("\\n🚀 1/4 - Benchmark Lista Email")
        all_results['email_list'] = await benchmark.benchmark_email_list(provider_config)
        
        # Test overhead connessione  
        print("\\n🔌 2/4 - Benchmark Connessione")
        all_results['connection_overhead'] = await benchmark.benchmark_connection_overhead(provider_config)
        
        # Test corpo vs headers
        print("\\n📝 3/4 - Benchmark Corpo vs Headers") 
        all_results['body_comparison'] = await benchmark.benchmark_body_vs_headers(provider_config)
        
        # Test impatto filtri
        print("\\n🔍 4/4 - Benchmark Filtri")
        all_results['filters_impact'] = await benchmark.benchmark_filters_impact(provider_config)
        
        # Riepilogo finale
        benchmark.print_benchmark_summary(all_results)
        
        print("\\n🎉 Benchmark completato con successo!")
        return True
        
    except Exception as e:
        print(f"\\n❌ Errore durante benchmark: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_full_benchmark())
    exit(0 if success else 1)