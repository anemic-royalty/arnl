#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# copyleft 2018: anemicroyalty@protonmail.com


import requests,subprocess,shlex,time,datetime,statistics,configparser,sys,re,fcntl,os,random
nhapitimeout=10
nhapi="https://api.nicehash.com/api?method=simplemultialgo.info"

factors={
	'scrypt':0.001,
	'sha256':1000,
	'x11':0.001,
	'x13':0.001,
	'keccak':0.001,
	'x15':0.001,
	'nist5':0.001,
	'neoscrypt':0.001,
	'lyra2re':0.001,
	'qubit':0.001,
	'quark':0.001,
	'lyra2rev2':0.001,
	'hodl':0.000001,
	'daggerhashimoto':0.001,
	'decred':1,
	'cryptonight':0.000001, 
	'lbry':1,
	'equihash':0.000000001,
	'pascal':1,
	'x11gost':0.001,
	'sia':1,
	'blake2s':1,
	'skunk':0.001, 
	}

expectedUnits={
	'blake2s':'GH/s',
	'cryptonight':'KH/s',
	'daggerhashimoto':'MH/s',
	'equihash':'Sol/s',
	'keccak':'MH/s',
	'lbry':'GH/s',
	'lyra2rev2':'MH/s',
	'neoscrypt':'MH/s',
	'nist5':'MH/s',
	'skunk':'MH/s',
	'x11gost':'MH/s'
	}

ccminerAlgos=['keccak','nist5','neoscrypt','lyra2rev2','cryptonight','lbry','blake2s','skunk','x11gost']

contributionWallet="34t7j6f2av4DdNhdZEbTrLf9VGCUoJ1nnC"

class BenchmarkFinished(Exception):
	def __init__(self):
		pass

def read_pipe(pipe):
	fd = pipe.fileno()
	fl = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
	try:
		return pipe.read()
	except:
		return ''
class Worker():
	def __init__(self,name,main):
		self.workerOptions={}
		self.name=name
		self.main=main
		self.runningProfit=0.00000000000000000000000001
		self.runningAlgo=''
		self.workerProfitability=[]
		self.averageWorkerProfitability=0
		self.averageWorkerProfitabilityUSD=0
		self.equihashMultiParser=False
		self.runningTerminated=False
		self.measuredHashrate=0
		self.switches={}
		self.sharesAccepted=False
		self.switchingForProfit=False
		self.terminatedAlgo=''
		self.haveProfitableAlgorithm=False
		self.startedRunning=datetime.datetime(1,1,1,1,1,1,1,)
		self.perfAcceptline=''
	def stop_mining(self):
		# Run custom command before terminating mining process
		if hasattr(self,'runningProcess'):
			if(self.runningAlgo+'.runafter' in self.workerOptions):
				cmd=self.workerOptions[self.runningAlgo+'.runafter']
				subprocess.run(shlex.split(cmd),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
			self.runningProcess.terminate()
			try:
				self.runningProcess.wait(timeout=5)
			except subprocess.TimeoutExpired:
				self.runningProcess.kill()
		
	def switch(self,terminated=False):
		if terminated:
			self.switchingForProfit=False
		if(hasattr(self,'runningProcess')):
			if self.switchingForProfit:
				if self.runningAlgo in self.switches:
					[accepted,total]=self.switches[self.runningAlgo]
					accepted+=int(self.sharesAccepted)
					total+=1
					self.switches[self.runningAlgo]=(accepted,total)
				else:
					self.switches[self.runningAlgo]=(int(self.sharesAccepted),1)
			self.stop_mining()
		self.perfAcceptline=''
		self.startMining(terminated)
	def returnMiningCommand(self):
		self.walletToRun=self.main.niceHashWalletAddress
		if self.main.runNextContrib:
			self.walletToRun=contributionWallet
		if self.runningAlgo+'.runarg' in self.workerOptions:
			runarg=self.workerOptions[self.runningAlgo+'.runarg']
		else:
			runarg=''
		if self.runningAlgo=='keccak':
			cmd="ccminer %s --url=stratum+tcp://keccak.%s.nicehash.com:3338 -u %s -r 3 -R 5 --algo keccak"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='nist5':
			cmd="ccminer %s --url=stratum+tcp://nist5.%s.nicehash.com:3340 -u %s -r 3 -R 5 --algo nist5"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='neoscrypt':
			cmd="ccminer %s --url=stratum+tcp://neoscrypt.%s.nicehash.com:3341 -u %s -r 3 -R 5 --algo neoscrypt"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='lyra2rev2':
			cmd="ccminer %s --url=stratum+tcp://lyra2rev2.%s.nicehash.com:3347 -u %s -r 3 -R 5 --algo lyra2rev2"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='cryptonight':
			cmd="ccminer %s --url=stratum+tcp://cryptonight.%s.nicehash.com:3355 -u %s -r 3 -R 5 --algo cryptonight"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='lbry':
			cmd="ccminer %s --url=stratum+tcp://lbry.%s.nicehash.com:3356 -u %s -r 3 -R 5 --algo lbry"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='blake2s':
			cmd="ccminer %s --url=stratum+tcp://blake2s.%s.nicehash.com:3361 -u %s -r 3 -R 5 --algo blake2s"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='skunk':
			cmd="ccminer %s --url=stratum+tcp://skunk.%s.nicehash.com:3362 -u %s -r 3 -R 5 --algo skunk"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='x11gost':
			cmd="ccminer %s --url=stratum+tcp://skunk.%s.nicehash.com:3359 -u %s -r 3 -R 5 --algo sib"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='daggerhashimoto':
			cmd="ethminer %s -SP 2 -U -S daggerhashimoto.%s.nicehash.com:3353 -O %s"%(runarg,self.main.niceHashRegion,self.walletToRun)
		elif self.runningAlgo=='equihash':
			cmd="zm %s --server equihash.%s.nicehash.com --port 3357 --user %s"%(runarg,self.main.niceHashRegion,self.walletToRun)
			self.equihashMultiParser=False
		return(cmd)
	def startMining(self,terminated):
		if terminated:
			self.terminatedCounter+=1
			if self.terminatedCounter==self.main.terminationLimit:
				if self.main.benchmarkRunning:
					print('%s: Unable to benchmark %s, exiting'%(self.name,self.runningAlgo))
					sys.exit(2)
				self.runningTerminated=True
				self.terminatedAlgo=self.runningAlgo
				running=self.reversedAlgos.index(self.runningAlgo)
				torun=0
				if running+1<len(self.reversedAlgos):
					torun=running+1
				self.runningProfit=self.currentProfitabilityByAlgo[self.reversedAlgos[torun]]
				self.runningAlgo=self.reversedAlgos[torun]
				self.terminatedCounter=0
		else:
			self.terminatedCounter=0
			self.runningProfit=self.highestProfit
			self.runningAlgo=self.bestAlgo
			self.runningProfitUSD=self.runningProfit*self.main.btcPrice
			self.runningTerminated=False
		# Run custom command before mining
		if(self.runningAlgo+'.runbefore' in self.workerOptions):
			cmd=self.workerOptions[self.runningAlgo+'.runbefore']
			subprocess.run(shlex.split(cmd),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
		
		# Run main mining program
		cmd=self.returnMiningCommand()
		self.runningProcess=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1)
		self.perfAcceptline=''
		self.startedRunning=datetime.datetime.now()
		self.daggerHashimotoPerf=[]
		self.sharesAccepted=False
		self.measuredHashrate=0
		
	def checkProcessRunning(self):
		if self.runningProcess.poll()!=None:
			self.switch(terminated=True)
			
	def parseMinerOutput(self):
		line=read_pipe(self.runningProcess.stdout)
		if line==None:
			return
		lx=line.decode('utf-8').strip()
		ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
		lx=ansi_escape.sub('', lx)
		if self.runningAlgo in ccminerAlgos:
			try:
				acceptPresplit,hashOutput=re.search('accepted: (.*) \(diff .*\), (.*) yes!.*',lx).groups()
				hashrate,unit=hashOutput.split(' ')
				accepted,total=acceptPresplit.split('/')
				self.perfAcceptline='%s %s. A/T shares: %s/%s.'%(hashrate,unit,accepted,total)
				self.measuredHashrate=float(hashrate)
				self.sharesAccepted=True
			except AttributeError:
				return
		if self.runningAlgo=='daggerhashimoto':
			try:
				hashrate,unit,accepted,stale,failed=re.search('Speed\s*(\d+.\d+) (\S*).*A(\d+).*R(\d+).*F(\d+)',lx).groups()
				[accepted,stale,failed]=[int(accepted),int(stale),int(failed)]
				hashrate=float(hashrate)
				if hashrate!=0.0:
					self.daggerHashimotoPerf.append(float(hashrate))
				if self.daggerHashimotoPerf==[]:
					repHash=0
				else:
					repHash=statistics.mean(self.daggerHashimotoPerf)
				self.measuredHashrate=float(repHash)
				self.perfAcceptline='%0.2f %s. A/T shares: %s/%s.'%(repHash,unit,accepted,accepted+stale+failed)
				self.sharesAccepted=True
			except AttributeError:
				return
		if self.runningAlgo=='equihash':
			try:
				if self.equihashMultiParser:
					hashrate,acceptedRatio=re.search('==========.*Avg: (\d+.\d+).* Sh: \d+.\d+\s+(\d+.\d+)*',lx).groups()
				else:
					hashrate,acceptedRatio=re.search('Avg: (\d+.\d+).* Sh: \d+.\d+\s+(\d+.\d+)*',lx).groups()
					if lx.find('==========')!=-1:
						self.equihashMultiParser=True
				self.perfAcceptline='%s Sol/s.'%hashrate
				unit='Sol/s'
				self.measuredHashrate=float(hashrate)
				if not acceptedRatio==None:
					self.perfAcceptline+=' Accepted Ratio: '+str(int(round(float(acceptedRatio)*100,0)))+'%.'
					self.sharesAccepted=True
			except AttributeError:
				return
		unit=unit.strip()[:-1].upper()+'s'
		transformVector={
			'H/s':1,
			'KH/s':1000,
			'MH/s':1000000,
			'GH/s':1000000000
			}
		if unit in transformVector:
			inHashes=self.measuredHashrate*transformVector[unit]
			self.measuredHashrate=inHashes/transformVector[expectedUnits[self.runningAlgo]]
		
		
	def runThroughAlgos(self):
		self.highestProfit=0
		bestAlgo=''
		self.currentProfitabilityDict={}
		self.currentProfitabilityByAlgo={}
		for algo in self.main.nhpayouts:
			algoName=algo['name']
			algoPerf=algoName+'.perf'
			algoWatt=algoName+'.watt'
			if (algoPerf in self.workerOptions and not algoWatt in self.workerOptions) or (not algoPerf in self.workerOptions and algoWatt in self.workerOptions):
				print ('error in settings for worker %s, algorithm %s. Missing either performance or consumption data.'%(self.name,algoName))
				sys.exit(2)
			if (not algoPerf in self.workerOptions) or (not algoWatt in self.workerOptions):
				continue
			profit=self.workerOptions[algoPerf]*factors[algoName]*float(algo['paying'])-self.workerOptions[algoWatt]*24*self.main.electricityCost/1000/self.main.btcPrice
			self.currentProfitabilityDict[profit]=algoName
			if profit>self.highestProfit:
				self.highestProfit=profit
				self.bestAlgo=algoName
			if(algoName==self.runningAlgo):
				self.runningProfit=profit
				self.runningProfitUSD=self.runningProfit*self.main.btcPrice
		self.reversedAlgos=[]
		for i in sorted(self.currentProfitabilityDict.keys()):
			self.reversedAlgos.append(self.currentProfitabilityDict[i])
			self.currentProfitabilityByAlgo[self.currentProfitabilityDict[i]]=i
		self.reversedAlgos.reverse()
	def updateBenchmarks(self):
		if hasattr(self,'startedRunning'):
			if self.measuredHashrate>0 and (datetime.datetime.now()-self.startedRunning).total_seconds()>600:
				self.workerOptions[self.runningAlgo+'.perf']=self.measuredHashrate


class Main():
	def __init__(self):
		self.btcPrice=10000
		self.nhpayouts=[]
		self.niceHashLastCheck=datetime.datetime(1,1,1,1,1,1,1,)
		self.haveData=False
		self.reversedAlgos=[]
		self.terminatedCounter=0
		self.workersList=[]
		self.readSettings()
		self.errorMessage=''
		self.runningBackup=False
		self.internetConnectionError=False
		self.nhWebError=False
		self.startedOn=datetime.datetime.now()
		self.runNextContrib=False
		self.benchmarkRunning=False
		if len(sys.argv)==2:
			self.runBenchmark=True
		else:
			self.runBenchmark=False
	def doBenchmark(self):
		if not self.benchmarkRunning:
			for worker in self.workersList:
				worker.benchesToRun=[]
				for option in worker.workerOptions:
					(algo,suff)=option.split('.')
					if suff=='perf':
						worker.benchesToRun.append(algo)
				worker.BenchAlgoRunning=False
				worker.benchFinished=False
			self.benchmarkRunning=True
		else:
			self.benchmarksToRun=0
			for worker in self.workersList:
				self.benchmarksToRun+=len(worker.benchesToRun)
				if ((datetime.datetime.now()-worker.startedRunning).total_seconds()>120 and worker.measuredHashrate!=0) or not worker.BenchAlgoRunning:
					if not worker.BenchAlgoRunning:
						worker.bestAlgo=worker.benchesToRun[0]
						worker.highestProfit=0
						worker.BenchAlgoRunning=True
						worker.switch()
						continue
					worker.workerOptions[worker.bestAlgo+'.perf']=worker.measuredHashrate
					if not worker.benchesToRun==[]:
						worker.benchesToRun.remove(worker.bestAlgo)
						if not worker.benchesToRun==[]:
							worker.bestAlgo=worker.benchesToRun[0]
							worker.switch()
				worker.checkProcessRunning()
				worker.parseMinerOutput()
			if self.benchmarksToRun==0:
				print('All benchmarks finished.')
				raise BenchmarkFinished()
			self.showScreen()
	def showScreen(self):
		line=''
		if self.benchmarkRunning:
			line='=== Running benchmarks. %s in queue.\n\n'%self.benchmarksToRun
		totalRunningProfit=0
		totalAverageProfit=0
		totalAverageProfitUSD=0
		for worker in self.workersList:
			td=datetime.datetime.now()-worker.startedRunning
			if worker.perfAcceptline=='':
				line+="%s [%s]: Mining %s, no shares accepted yet.\n"%(worker.name,str(td).split('.')[0],worker.runningAlgo)
			else:
				if not self.benchmarkRunning:
					line+="%s [%s]: %s @ %s Profitability: %0.06f BTC/day ($%0.2f/day).\n"%(
					worker.name,str(td).split('.')[0],worker.runningAlgo.capitalize(),worker.perfAcceptline,worker.runningProfit,worker.runningProfitUSD)
				else:
					line+='%s [%s]: %s @ '%(worker.name,str(td).split('.')[0],worker.runningAlgo.capitalize())+worker.perfAcceptline+'\n'
			if not self.benchmarkRunning:
				line+="Average profitability since start: %0.06f BTC/day ($%0.2f/day).\n"%(worker.averageWorkerProfitability,worker.averageWorkerProfitabilityUSD)
			if not self.benchmarkRunning:
				if worker.switches!={}:
					line+='Switching A/T:'
					for switchAlgo in worker.switches:
						(acc,tot)=worker.switches[switchAlgo]
						line+=' %s (%s/%s)'%(switchAlgo.capitalize(),acc,tot)
					line+='\n'
				totalRunningProfit+=worker.runningProfit
				totalAverageProfit+=worker.averageWorkerProfitability
				totalAverageProfitUSD+=worker.averageWorkerProfitabilityUSD
		if not self.benchmarkRunning:
			td=datetime.datetime.now()-self.startedOn
			line+='===========\n'
			line+='Totals: running for %s; last price update was %0is ago.\nCurrent profitability: %0.06f BTC/day ($%0.2f/day), average: %0.06f BTC/day ($%0.2f/day).\n'%(
				str(td).split('.')[0],(datetime.datetime.now()-self.niceHashLastCheck).total_seconds(),totalRunningProfit,totalRunningProfit*self.btcPrice,totalAverageProfit,totalAverageProfitUSD)
			if self.runningBackup:line+='Warning: currently running fallback algorithm.\n'
			if self.internetConnectionError:line+='Warning: currently unable to get Nicehash prices data; possible internet connection problem.\n'
			if self.nhWebError:line+='Warning: error parsing data from Nicehash, their website is possibly down.\n'
			for worker in self.workersList:
				if worker.runningTerminated:
					line+='Warning: %s: Miner for %s terminated too many times. Running the next best algorithm.\n'%(worker.name,worker.terminatedAlgo)
			if self.runNextContrib:line=line.replace('Current profitability','Current* profitability')
		print("\x1b[2J\x1b[H")
		print(line)
	def retSettingsValue(self,var,default,worker='settings'):
		if(var in self.config[worker]):
			return self.config[worker][var]
		else:
			return default
	def readSettings(self):
		try:
			if os.path.isfile('updated.cfg'):
				cfgFile='updated.cfg'
			else:
				cfgFile='arnl.cfg'
				if not os.path.isfile(cfgFile):
					print('Configuration file not found!')
					sys.exit(2)
			self.config=configparser.ConfigParser()
			self.config.read(cfgFile)
		except configparser.ParsingError as err:
			print('Error reading settings file!\n',err.message)
			sys.exit(2)
		if not 'settings' in self.config:
			print('Settings file have no settings section! Exiting')
			sys.exit(2)
		if len(self.config.sections())==1:
			print('No workers specified in settings! Exiting')
			sys.exit(2)
		self.niceHashWalletAddress=self.retSettingsValue('NiceHashWalletAddress','')
		if self.niceHashWalletAddress=='':
			print('NiceHash wallet not set! Exiting')
			sys.exit(2)
		self.niceHashRegion=self.retSettingsValue('NiceHashRegion','eu')
		self.fallbackAlgorithm=self.retSettingsValue('FallbackAlgorithm','daggerhashimoto')
		try:
			self.electricityCost=float(self.retSettingsValue('ElectricityCost',0.2))
			self.profitabilityThreshold=float(self.retSettingsValue('ProfitabilityThreshold',5))
			self.nicehashCheckTimer=int(self.retSettingsValue('NicehashCheckTimer',60))
			self.terminationLimit=int(self.retSettingsValue('TerminationLimit',3))
			self.develContributionMins=int(self.retSettingsValue('DeveloperContributionMins',14))
		except ValueError as err:
			print('Settings file malformated: %s'%err)
			sys.exit(2)
		for worker in self.config.sections():
			if worker!='settings':
				w=Worker(name=worker,main=self)
				for option in self.config[worker]:
					try:
						if option.split('.')[1]=='watt' or option.split('.')[1]=='perf':
							try:
								w.workerOptions[option]=float(self.config[worker][option])
							except ValueError as err:
								print('Malformated worker settings, worker ID: %s option: %s'%(worker,option))
								sys.exit(2)
						elif option.split('.')[1]=='runarg' or option.split('.')[1]=='runbefore' or option.split('.')[1]=='runafter':
							w.workerOptions[option]=self.config[worker][option]
						else:
							print('Malformated worker settings, worker ID: %s Unknown option: %s'%(worker,option))
							sys.exit(2)
					except IndexError as err:
						print('Malformated worker settings, worker ID: %s option: %s'%(worker,option))
						sys.exit(2)
				if w.workerOptions=={}:
					print('settings error, worker %s has no enabled options'%worker)
					sys.exit(2)
				self.workersList.append(w)
	def run(self):
		if self.runBenchmark:
			self.doBenchmark()
		else:
			if (datetime.datetime.now()-self.niceHashLastCheck).total_seconds()>=max(self.nicehashCheckTimer,60):
				runningContrib=self.runNextContrib
				if random.randint(1,1440)<=self.develContributionMins:
					self.runNextContrib=True
				else:
					self.runNextContrib=False
				if self.getprofitability() or self.haveData:
					for worker in self.workersList:
						worker.updateBenchmarks()
						worker.runThroughAlgos()
						if (worker.highestProfit/worker.runningProfit>self.profitabilityThreshold/100+1) or (
							runningContrib and not self.runNextContrib) or (not runningContrib and self.runNextContrib):
							# first run
							if worker.runningAlgo=='':
								worker.runThroughAlgos()
							if (worker.highestProfit/worker.runningProfit>self.profitabilityThreshold/100+1):
								worker.switchingForProfit=True
							else:
								worker.switchingForProfit=False
							self.runningBackup=False
							worker.switch()
						worker.workerProfitability.append(worker.runningProfit)
						worker.averageWorkerProfitability=statistics.mean(worker.workerProfitability)
						worker.averageWorkerProfitabilityUSD=worker.averageWorkerProfitability*self.btcPrice
				else:
					self.runningBackup=True
					for worker in self.workersList:
						worker.runningAlgo=self.fallbackAlgorithm
						worker.bestAlgo=self.fallbackAlgorithm
						worker.highestProfit=0
						worker.switch()
			for worker in self.workersList:
				worker.parseMinerOutput()
				worker.checkProcessRunning()
			self.showScreen()
		time.sleep(0.1)
	def getprofitability(self):
		devel=0
		if not devel:
			try:
				nhjson=requests.get(nhapi,timeout=nhapitimeout)
				try:
					self.nhpayouts=nhjson.json()['result']['simplemultialgo']
				except:
					self.nhWebError=True
					self.niceHashLastCheck=datetime.datetime.now()
					return self.haveData
			except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
				self.internetConnectionError=True
				self.niceHashLastCheck=datetime.datetime.now()
				return self.haveData
			try:
				btcPriceapi=requests.get('https://www.bitstamp.net/api/v2/ticker/btcusd',timeout=10)
				if btcPriceapi.status_code!=200:
					raise ValueError
				self.btcPrice=float(btcPriceapi.json()['vwap'])
			except:
				pass
		else:
			self.nhpayouts=[{'paying': '0.00253425', 'port': 3333, 'name': 'scrypt', 'algo': 0}, {'paying': '0.00000015', 'port': 3334, 'name': 'sha256', 'algo': 1}, {'paying': '0', 'port': 3335, 'name': 'scryptnf', 'algo': 2}, {'paying': '0.00004279', 'port': 3336, 'name': 'x11', 'algo': 3}, {'paying': '0.00070311', 'port': 3337, 'name': 'x13', 'algo': 4}, {'paying': '0.00039199', 'port': 3338, 'name': 'keccak', 'algo': 5}, {'paying': '0.00087062', 'port': 3339, 'name': 'x15', 'algo': 6}, {'paying': '0.00771907', 'port': 3340, 'name': 'nist5', 'algo': 7}, {'paying': '0.38335949', 'port': 3341, 'name': 'neoscrypt', 'algo': 8}, {'paying': '0', 'port': 3342, 'name': 'lyra2re', 'algo': 9}, {'paying': '0', 'port': 3343, 'name': 'whirlpoolx', 'algo': 10}, {'paying': '0.00052098', 'port': 3344, 'name': 'qubit', 'algo': 11}, {'paying': '0.0004962', 'port': 3345, 'name': 'quark', 'algo': 12}, {'paying': '0', 'port': 3346, 'name': 'axiom', 'algo': 13}, {'paying': '0.00830084', 'port': 3347, 'name': 'lyra2rev2', 'algo': 14}, {'paying': '0', 'port': 3348, 'name': 'scryptjanenf16', 'algo': 15}, {'paying': '0', 'port': 3349, 'name': 'blake256r8', 'algo': 16}, {'paying': '0', 'port': 3350, 'name': 'blake256r14', 'algo': 17}, {'paying': '0', 'port': 3351, 'name': 'blake256r8vnl', 'algo': 18}, {'paying': '110', 'port': 3352, 'name': 'hodl', 'algo': 19}, {'paying': '5.01054937', 'port': 3353, 'name': 'daggerhashimoto', 'algo': 20}, {'paying': '0.00006202', 'port': 3354, 'name': 'decred', 'algo': 21}, {'paying': '382.86663348', 'port': 3355, 'name': 'cryptonight', 'algo': 22}, {'paying': '0.00082303', 'port': 3356, 'name': 'lbry', 'algo': 23}, {'paying': '111111.8660139', 'port': 3357, 'name': 'equihash', 'algo': 24}, {'paying': '0.00016783', 'port': 3358, 'name': 'pascal', 'algo': 25}, {'paying': '0.01944337', 'port': 3359, 'name': 'x11gost', 'algo': 26}, {'paying': '0.00006835', 'port': 3360, 'name': 'sia', 'algo': 27}, {'paying': '0.00011178', 'port': 3361, 'name': 'blake2s', 'algo': 28}, {'paying': '0.01022729', 'port': 3362, 'name': 'skunk', 'algo': 29}]
		self.niceHashLastCheck=datetime.datetime.now()
		self.haveData=True
		self.internetConnectionError=False
		self.nhWebError=False
		return self.haveData

def save_settings():
	config = configparser.ConfigParser()
	config['settings']={}
	config['settings']['NiceHashWalletAddress']=main.niceHashWalletAddress
	config['settings']['NiceHashRegion']=main.niceHashRegion
	config['settings']['FallbackAlgorithm']=main.fallbackAlgorithm
	config['settings']['ElectricityCost']=str(main.electricityCost)
	config['settings']['ProfitabilityThreshold']=str(main.profitabilityThreshold)
	config['settings']['NicehashCheckTimer']=str(main.nicehashCheckTimer)
	config['settings']['TerminationLimit']=str(main.terminationLimit)
	config['settings']['DeveloperContributionMins']=str(main.develContributionMins)
	for worker in main.workersList:
		config[worker.name]={}
		for option in worker.workerOptions:
			config[worker.name][option]=str(worker.workerOptions[option])
	with open('updated.cfg','w') as configfile:
		config.write(configfile)


if len(sys.argv)==2:
	if not sys.argv[1]=='benchmark':
		print('Unknown argument, to run benchmark, use: benchmark')
		sys.exit(2)
if len(sys.argv)>2:
	print('Too many arguments passed.')
	sys.exit(2)

main=Main()
try:
	while True:
		main.run()
except KeyboardInterrupt:
	# do not create settings file for unfinished benchmarks
	if not len(sys.argv)==2:
		for worker in main.workersList:
			worker.stop_mining()
		print('\nExiting, bye.')
		save_settings()
		sys.exit(0)

except BenchmarkFinished:
	save_settings()
	sys.exit(0)

except Exception as err:
	print('\nSomething went terribly wrong, stopping all miners and exiting')
	for worker in main.workersList:
		worker.stop_mining()
	print('Error was:',err.__repr__())
	sys.exit(2)
	