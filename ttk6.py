import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO
import time
import csv

#Création d'une classe MAX6675
class TTK:
    ERREUR = -1000
    
    units = "c"
    min = -50
    max = 204
    valeurcorrigee = 0
    valeurbrute = 0
    _spi = None
    valide = False
    
    def __init__(self, clk= 24, cs= 4, do= 25,units = "c", spi=None, gpio=None):
        self.units = units
            # Manipuler le materiel SPI
        if spi is not None:
            self._spi = spi
        elif clk is not None and cs is not None and do is not None:
            if gpio is None:
                gpio = GPIO.RPiGPIOAdapter(RPi.GPIO)
                self._spi = SPI.BitBang(gpio, clk, None, do, cs)
            else:
                raise ValueError('doit spécifier le SPI') #Exception
                self._spi.set_clock_hz(5000000)
                self._spi.set_mode(0)
                self._spi.set_bit_order(SPI.MSBFIRST)

        #Methode pour recupérer la température
    def lire_temp(self):
                    #Renvoyer la valeur de la temperature du thermocouple en degres Celsius
        valeurbrute = self._read16()
                    
                    # Verifier la valeur
        if valeurbrute & 0x4:
            return float('NaN')
                    # Verifier si le bit signé est activé
        if valeurbrute & 0x80000000:
            valeurbrute >>= 3 # N'a besoin que de 12 MSB
            valeurbrute -= 4096
        else:
                            # Valeur positive, il suffit de decaler les bits pour obtenir la valeur
            valeurbrute >>= 3 # N'a besoin que de 12 MS
    
        self.valeurbrute = valeurbrute * 0.25            # Echelle de 0,25 degres celsius et retourne la valeur
        if valeurbrute < self.min or valeurbrute > self.max:  #On vérifie que la valeur rentre dans la plage valide
            valide = False
        else:
            valide = True
        return valide
    
    def _read16(self):
                # Lire 16 bits à partir du bus SPI
        raw = self._spi.read(2)
        if raw is None or len(raw) != 2:
            raise RuntimeError('Ne peux pas lire')
        value = raw[0] << 8 | raw[1]
        return value

                
    def lire_temp_corrigee(self):
        #Algorithme de fonctionnement du CSV :
        #Ouvrir fichier
        #Verifier format
        #Lire première ligne data -> ligne1
        #Extraire x1 et ca
        #
        #Boucle tant que valeurbrute>x1
        #lire ligne -> ligne2
        #extraire x2 et y2
        #Si valeurbrute > x2
        #ligne1 = ligne2
        #x1 = x2
        #y1 = y2
        #Fin boucle
        pente = 1
        offset = 0
        if not self.lire_temp():            #On va chercher la valeur de la température qui est disponible dans valeurbrute
            return ERREUR
        else:
            x1 = None
            y1 = None
            x2 = None
            y2 = None
            with open('etalonnage.csv', 'r') as monCSV: #read().split('\n') # Ouvrir fichier
                reader = csv.reader(monCSV, delimiter=';')
                i = -1
                entete = next(reader)
                ligne1 = next(reader)
                ligne2 = next(reader)
                
                while ligne2 != None:
                    x1 = int(ligne1[0])
                    y1 = int(ligne1[1])
                    x2 = int(ligne2[0])
                    y2 = int(ligne2[1])
                    
                    if self.valeurbrute > float(x1) and self.valeurbrute < float(x2):
                        break
                    
                    ligne1 = ligne2
                    ligne2 = next(reader)
                #test boucle de lecture format texte
                #ligne = monCSV.readline()
                #while ligne != "":
                        #print(ligne)
                        #ligne = monCSV.readline()
                #entete = ['brute','corrige']
                #reader = csv.reader(monCSV, delimiter=';')
                #for row in reader:
                    #print(row[0],row[1])
            
            print('calcul')
            print(int(y1),y2,x2,x1)
            #pente = 1.0051
            #offset = -3.1587
            pente = (y1 - y2) / (x1 - x2)
            print(pente)
            offset = pente * (y1 - y2 / x1 - x2)
            print(offset)
            valeurcorrigee = pente * self.valeurbrute + offset
            return valeurcorrigee
     
ttk = TTK()
print(ttk.lire_temp_corrigee())
    
#interpolation linéaire
# x = tempbrute
# y = tempcorige