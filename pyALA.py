#!/usr/bin/python
# pacman -S python-requests python-beautifulsoup4

import os
import shlex
import requests
import argparse
import datetime
import subprocess
import progressbar
import collections

from bs4 import BeautifulSoup

# ----------------------------
# Class definitions start
# ----------------------------


class Options:
	user_def_dir = ''
	get_sig = False
	check_da_log_yo = False

	download_dir = os.getcwd()

	arch = 'x86_64'
	ala = 'https://archive.archlinux.org/packages/'
	pacman_log = '/var/log/pacman.log'
	pacman_cache_dir = '/var/cache/pacman/pkg/'


class Colors:
	CYAN = '\033[96m'
	YELLOW = '\033[93m'
	GREEN = '\033[92m'
	RED = '\033[91m'
	WHITE = '\033[97m'
	ENDC = '\033[0m'


class Pacman:
	def __init__(self, package, show_num):
		self.package = package
		self.show_num = show_num

	def version(self):
		try:
			args_to_subprocess = shlex.split('pacman -Q ' + self.package)
			pacman_proc = subprocess.run(args_to_subprocess, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
			installed_version = pacman_proc.stdout.decode('utf-8').replace('\n', '').split()[1]
			return installed_version
		except:
			return False

	def parse_log(self):
		print(Colors.CYAN + (self.package + ' :LOG:').rjust(63, '-') + Colors.ENDC)

		present_in_log = False
		with open(Options.pacman_log, 'r') as log_file:
			log = log_file.readlines()
			for i in log:
				log_line = i.replace('\n', '').split()
				try:
					if self.package == log_line[4] and log_line[2] == '[ALPM]':
						present_in_log = True

						log_date = log_line[0].replace('[', '')
						log_transaction = log_line[3]
						log_versions = log_line[5:]

						date_object = datetime.datetime.strptime(log_date, '%Y-%m-%d')
						sexy_date = date_object.strftime('%d-%b-%Y')

						template = "{0:%s}{1:%s}{2:%s}" % (2, 59, 15)

						if log_transaction == 'downgraded' or log_transaction == 'removed':
							if len(log_versions) > 1:
								template = "{0:%s}{1:%s}{2:%s}" % (2, 73, 15)
								log_versions[1] = Colors.WHITE + log_versions[1] + Colors.ENDC + Colors.RED
							print(template.format('•', Colors.RED + ' '.join(log_versions).replace('(', '').replace(')', '') + Colors.ENDC, sexy_date))
						else:
							if len(log_versions) > 1:
								template = "{0:%s}{1:%s}{2:%s}" % (2, 73, 15)
								log_versions[1] = Colors.WHITE + log_versions[1] + Colors.ENDC + Colors.GREEN
							print(template.format('•', Colors.GREEN + ' '.join(log_versions).replace('(', '').replace(')', '') + Colors.ENDC, sexy_date))
				except:
					pass

		if present_in_log is False:
			print(Colors.RED + '• No log entries for ' + self.package + Colors.ENDC)

	def full_system_upgrade_log(self):
		upgrades = {}
		with open('/var/log/pacman.log', 'r') as log_file:
			get_line = False
			log = log_file.readlines()
			for count, line in enumerate(log):
				if '[PACMAN] starting full system upgrade' in line:
					upgrade_time = ' '.join(line.replace('[', '').replace(']', '').split()[:2])
					date_object = datetime.datetime.strptime(upgrade_time, '%Y-%m-%d %H:%M')
					get_line = True
				elif '[ALPM]' in line and 'transaction completed' in line:
					get_line = False
				elif get_line:
					if '[ALPM]' in line and 'warning' not in line and 'running ' not in line and 'transaction started' not in line:
						package_details = line.replace('\n', '').split()[3:]
						try:
							upgrades[date_object].append(package_details)
						except KeyError:
							upgrades[date_object] = []
							upgrades[date_object].append(package_details)

		final_dict = collections.OrderedDict(sorted(upgrades.items(), key=lambda t: t[0], reverse=True))

		for count, i in enumerate(final_dict):
			sexy_date = i.strftime('%H:%M %d-%b-%Y')
			print(Colors.CYAN + sexy_date + Colors.ENDC)

			for j in final_dict[i]:
				log_transaction = j[0]
				log_package_name = j[1]
				log_versions = j[2:]

				template = "{0:%s}{1:%s}{2:%s}" % (2, 35, 15)
				if log_transaction == 'removed':
					print(template.format('•', log_package_name, Colors.RED + ' '.join(log_versions).replace('(', '').replace(')', '') + Colors.ENDC))
				else:
					if len(log_versions) > 1:
						log_versions[1] = Colors.WHITE + log_versions[1] + Colors.ENDC + Colors.GREEN
					print(template.format('•', log_package_name, Colors.GREEN + ' '.join(log_versions).replace('(', '').replace(')', '') + Colors.ENDC))

			if count + 1 == self.show_num:
				return
			else:
				print()

	def full_log(self):
		current = 0
		transactions = []
		with open('/var/log/pacman.log', 'r') as log_file:
			log = log_file.readlines()
			log.sort(reverse=True)
			for line in log:
				if '[ALPM]' in line and ('upgraded' in line or 'removed' in line or 'installed' in line):
					transactions.append(line.replace('\n', '').split())
					current += 1
					if current > self.show_num:
						break

		template = "{0:%s}{1:%s}{2:%s}" % (15, 35, 15)
		for j in transactions:
			log_date = j[0].replace('[', '')
			date_object = datetime.datetime.strptime(log_date, '%Y-%m-%d')
			sexy_date = date_object.strftime('%d-%b-%Y')

			log_transaction = j[3]
			log_package_name = j[4]
			log_versions = j[5:]

			if log_transaction == 'upgraded' or log_transaction == 'installed':
				if len(log_versions) > 1:
					log_versions[1] = Colors.WHITE + log_versions[1] + Colors.ENDC + Colors.GREEN
				print(template.format(sexy_date, log_package_name, Colors.GREEN + ' '.join(log_versions).replace('(', '').replace(')', '') + Colors.ENDC))
			else:
				print(template.format(sexy_date, log_package_name, Colors.RED + ' '.join(log_versions).replace('(', '').replace(')', '') + Colors.ENDC))

# ----------------------------
# Function definitions start
# ----------------------------


def check_archive(incoming_list):
	available_packages = {}

	for package in incoming_list:
		html = requests.get(Options.ala + package[0] + '/' + package)
		if html.status_code == 200:

			for i in html.iter_lines():
				link_line = BeautifulSoup(i.decode("utf-8"), "lxml")
				link_line_text = i.decode("utf-8").split()

				try:
					package_name = link_line.find('a').get('href')
					parsed_package_name = package_name.replace(package, '')

					if (Options.arch in parsed_package_name or 'any' in parsed_package_name) and '.sig' not in parsed_package_name:
						package_name_list = parsed_package_name.split('-')

						""" I'd love to know if there's a more comprehensive way of checking for and
						replacing auto-changed special characters as in the case of what lies beneath """
						package_version = package_name_list[1].replace('%2B', '+').replace('%3A', ':') + '-' + package_name_list[2]
						package_link = Options.ala + package[0] + '/' + package + '/' + package_name

						date_object = datetime.datetime.strptime(link_line_text[2], '%d-%b-%Y')

						try:
							available_packages[package].append([package_version, date_object, package_link])
						except KeyError:
							available_packages[package] = []
							available_packages[package].append([package_version, date_object, package_link])
						""" Dictionary contains list(s) with scheme:
						0: Package version
						1: Last modified date
						2: Package link """

				except:
					pass

		else:
			print(package + ':' + Colors.RED + ' ' + str(html.status_code) + Colors.ENDC)
			print()

	if len(available_packages) > 0:
		final_dict = collections.OrderedDict(sorted(available_packages.items(), key=lambda t: t[0]))
		display_shizz(final_dict)


def display_shizz(package_list):
	package_number = 1
	package_link_list = []

	pacman_cache = os.listdir(Options.pacman_cache_dir)

	for i in package_list:
		package_list[i].sort(key=lambda x: x[1])

		package_status = Pacman(i, None)
		package_version = package_status.version()
		if Options.check_da_log_yo is True:
			package_status.parse_log()

		print(Colors.CYAN + (i + ' :PACKAGES:').rjust(63, '-') + Colors.ENDC)

		for j in package_list[i]:
			sexy_date = j[1].strftime('%d-%b-%Y')
			if j[0] == package_version:
				sexy_date = sexy_date + ' (Installed)'

			digits = len(str(package_number)) - 1

			# Packages already in the pacman cache are highlighted in green
			package_name = j[2].rsplit('/', 1)[1].replace('%2B', '+').replace('%3A', ':')
			if package_name in pacman_cache:
				template = "{0:%s}{1:%s}{2:%s}" % (3, 59 - digits, 15)
				print(template.format(Colors.YELLOW + str(package_number) + ' ', Colors.GREEN + j[0] + Colors.ENDC, sexy_date))
			else:
				template = "{0:%s}{1:%s}{2:%s}" % (3, 50 - digits, 15)
				print(template.format(Colors.YELLOW + str(package_number) + ' ' + Colors.ENDC, j[0], sexy_date))

			# A separate list makes it simpler to retain a coherent numbering scheme across multiple selections
			package_link_list.append([i + ' ' + j[0], j[2]])
			package_number += 1
		print()

	try:
		download_me = input('Packages: ')
	except KeyboardInterrupt:
		exit()

	entered_numbers = [int(k) for k in download_me.split()]
	download_list = []
	for l in entered_numbers:
		try:
			package_link = package_link_list[l - 1][1]
			download_list.append(package_link)
		except:
			print('Are you sure? Like really really sure?')
			exit()

	download_packages(download_list)


def download_packages(newphonewhodis):
	if Options.get_sig is True:
		sig_list = []
		for i in newphonewhodis:
			sig_list.append(i)
			sig_list.append(i + '.sig')
		newphonewhodis = sig_list

	for j in newphonewhodis:
		package_name = j.rsplit('/', 1)[1].replace('%2B', '+').replace('%3A', ':')
		if os.path.exists(Options.user_def_dir):
			package_destination = Options.user_def_dir + '/' + package_name
		else:
			package_destination = Options.download_dir + '/' + package_name

		r1 = requests.head(j)
		file_size = int(r1.headers['Content-length'])
		file_size_MiB = file_size * 9.5367e-7
		print(Colors.GREEN + package_name + ' (' + str(file_size_MiB)[:4] + ' MiB)' + Colors.ENDC)

		bar = progressbar.ProgressBar(maxval=file_size, widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), ' ', progressbar.ETA()])

		r2 = requests.get(j, stream=True)
		downloaded = 0
		try:
			with open(package_destination, 'wb') as pdest:
				for chunk in r2.iter_content(100):
					pdest.write(chunk)
					downloaded += len(chunk)
					bar.update(downloaded)
		except KeyboardInterrupt:
			print('Download interrupted')
		print()

# ----------------------------
# Function definitions end
# ----------------------------


def main():
	parser = argparse.ArgumentParser(description='Download Arch Linux Archive packages from from your terminal. IT\'S THE FUTURE.')
	parser.add_argument('package_name', type=str, nargs='*', help='Package Name(s)')
	parser.add_argument('-d', type=str, nargs=1, help='Download directory', metavar='<download_dir>', required=False)
	parser.add_argument('--log', action='store_true', help='Show history from pacman.log', required=False)
	parser.add_argument('--sig', action='store_true', help='Get .sig files', required=False)
	parser.add_argument('-Syu', type=int, nargs='?', help='Show last n full system upgrades', metavar='<n>', const=1, required=False)
	parser.add_argument('--all', type=int, nargs='?', help='Show last n transctions (Default: 10)', metavar='<n>', const=10, required=False)
	args = parser.parse_args()

	if args.Syu:
		upgrade_log = Pacman(None, args.Syu)
		upgrade_log.full_system_upgrade_log()
	elif args.all:
		all_log = Pacman(None, args.all)
		all_log.full_log()
	elif args.package_name:
		if args.d:
			Options.user_def_dir = args.d[0]
		if args.sig:
			Options.get_sig = True
		if args.log:
			Options.check_da_log_yo = True
		check_archive(args.package_name)
	else:
		parser.print_help()

main()
