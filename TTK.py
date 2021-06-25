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
        self.valeurbrute = valeurbrute * 0.25
        print(self.valeurbrute)# Echelle de 0,25 degres celsius et retourne la valeur
        if valeurbrute < self.min or valeurbrute > self.max:  #On vérifie que la valeur rentre dans la plage valide
            valide = False
        else:
            valide = True
        print(valide)
        return valide
    
    def _read16(self):# Lire 16 bits à partir du bus SPI
        raw = self._spi.read(2)
        if raw is None or len(raw) != 2:
            raise RuntimeError('Ne peux pas lire')
        value = raw[0] << 8 | raw[1]
        return value
        
    def lire_temp_corrigee(self):   
        if not self.lire_temp():            #On va chercher la valeur de la température qui est disponible dans valeurbrute
            return ERREUR
        else:
            x1 = None #On fixe à None pour forcer le programme a crash s'il y a un problème
            y1 = None
            x2 = None
            y2 = None
            with open('etalonnage.csv', 'r') as monCSV:  # Ouvrir le fichier
                reader = csv.reader(monCSV, delimiter=';')
                entete = next(reader) #On dit que l'entete est la ligne 0
                ligne1 = next(reader) #On dit que la ligne 1 est la ligne après l'entete
                ligne2 = next(reader) #On dit que la ligne 2 est la ligne après la ligne 1
                
                while ligne2 != None: #Boucle tant que ligne est différent de None
                    x1 = int(ligne1[0]) #On fixe la valeur brut 1 à la ligne 1
                    y1 = int(ligne1[1]) #On fixe la valeur corrige 1 à la ligne 1
                    x2 = int(ligne2[0]) #On fixe la valeur brut 2 à la ligne 2
                    y2 = int(ligne2[1]) #On fixe la valeur corrige 2 à la ligne 2
                    
                    if self.valeurbrute > float(x1) and self.valeurbrute < float(x2): #Si la valeurbrute est plus grand que la valeur brute 1 et qu'elle est plus petite que la valeur brute 2
                        break #On casse la boucle
                    
                    ligne1 = ligne2 #Si la condition est pas respectée, la ligne devient la ligne 2
                    ligne2 = next(reader) # et la ligne 2 devient la ligne d'après
              
            
            print('calcul de l interpolation linéaire')
            print(x1,y1,x2,y2) 
            pente = (y1 - y2) / (x1 - x2) #On calcule la pente
            print(pente)
            offset = (y1* x2 - y2 * x1) / (x2 - x1)a #On calcule l'offset
            print(offset)
            valeurcorrigee = pente * self.valeurbrute + offset #On calcule valeurcorrigee
            return valeurcorrigee #On retourne valeurcorrigee
 
running(true)
while(running):
    try:
        ttk = TTK()
        print(ttk.lire_temp_corrigee())
        time
    