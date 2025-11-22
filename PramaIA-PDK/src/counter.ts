import { LogService } from './services/log-service'

// Ottieni un logger specifico per questo modulo
const logger = LogService.getInstance().getModuleLogger('counter');

export function setupCounter(element: HTMLButtonElement) {
  let counter = 0
  
  const setCounter = (count: number) => {
    counter = count
    element.innerHTML = `count is ${counter}`
    
    // Log ogni volta che il contatore cambia
    logger.debug(`Contatore impostato a ${counter}`);
    
    // Aggiungi log di diversi livelli in base al valore
    if (counter === 10) {
      logger.info('Contatore ha raggiunto 10', { milestone: 'small' });
    } else if (counter === 50) {
      logger.info('Contatore ha raggiunto 50', { milestone: 'medium' });
    } else if (counter === 100) {
      logger.warning('Contatore ha raggiunto 100!', { milestone: 'large' });
    } else if (counter > 1000) {
      logger.error('Contatore troppo alto!', { value: counter });
    }
  }
  
  element.addEventListener('click', () => {
    // Log prima dell'incremento
    logger.debug('Click sul contatore', { currentValue: counter });
    setCounter(counter + 1);
  })
  
  setCounter(0)
  logger.info('Contatore inizializzato');
}
