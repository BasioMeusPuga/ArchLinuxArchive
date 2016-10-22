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

arch = 'x86_64'
ala = 'http://seblu.net/a/archive/packages/'
download_dir = os.getcwd()
pacman_log = '/var/log/pacman.log'
pacman_cache_dir = '/var/cache/pacman/pkg/'


class colors:
	CYAN = '\033[96m'
	YELLOW = '\033[93m'
	GREEN = '\033[92m'
	RED = '\033[91m'
	WHITE = '\033[97m'
	ENDC = '\033[0m'


class Pacman:
	def __init__(self, package):
		self.package = package

	def version(self):
		try:
			args_to_subprocess = shlex.split('pacman -Q ' + self.package)
			pacman_proc = subprocess.run(args_to_subprocess, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
			installed_version = pacman_proc.stdout.decode('utf-8').replace('\n', '').split()[1]
			return installed_version
		except:
			return False

	def parse_log(self):
		print(colors.CYAN + (self.package + ' :LOG:').rjust(63, '-') + colors.ENDC)

		present_in_log = False
		with open(pacman_log, 'r') as log_file:
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
								log_versions[1] = colors.WHITE + log_versions[1] + colors.ENDC + colors.RED
							print(template.format('•', colors.RED + ' '.join(log_versions).replace('(', '').replace(')', '') + colors.ENDC, sexy_date))
						else:
							if len(log_versions) > 1:
								template = "{0:%s}{1:%s}{2:%s}" % (2, 73, 15)
								log_versions[1] = colors.WHITE + log_versions[1] + colors.ENDC + colors.GREEN
							print(template.format('•', colors.GREEN + ' '.join(log_versions).replace('(', '').replace(')', '') + colors.ENDC, sexy_date))
				except:
					pass

		if present_in_log is False:
			print(colors.RED + '• No log entries for ' + self.package + colors.ENDC)


def check_archive(incoming_list):
	available_packages = {}

	for package in incoming_list:

		html = requests.get(ala + package[0] + '/' + package)
		if html.status_code == 200:

			for i in html.iter_lines():
				link_line = BeautifulSoup(i.decode("utf-8"), "lxml")
				link_line_text = i.decode("utf-8").split()

				try:
					package_name = link_line.find('a').get('href')
					parsed_package_name = package_name.replace(package, '')

					if (arch in parsed_package_name or 'any' in parsed_package_name) and '.sig' not in parsed_package_name:
						package_name_list = parsed_package_name.split('-')

						""" I'd love to know if there's a more comprehensive way of checking for and
						replacing auto-changed special characters as in the case of what lies beneath """
						package_version = package_name_list[1].replace('%2B', '+').replace('%3A', ':') + '-' + package_name_list[2]
						package_link = ala + package[0] + '/' + package + '/' + package_name

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
			print(package + ':' + colors.RED + ' ' + str(html.status_code) + colors.ENDC)
			print()

	if len(available_packages) > 0:
		final_dict = collections.OrderedDict(sorted(available_packages.items(), key=lambda t: t[0]))
		display_shizz(final_dict)


def display_shizz(package_list):
	package_number = 1
	package_link_list = []

	pacman_cache = os.listdir(pacman_cache_dir)

	for i in package_list:

		package_list[i].sort(key=lambda x: x[1])

		package_status = Pacman(i)
		package_version = package_status.version()
		if check_da_log_yo is True:
			package_status.parse_log()

		print(colors.CYAN + (i + ' :PACKAGES:').rjust(63, '-') + colors.ENDC)
		for j in package_list[i]:

			sexy_date = j[1].strftime('%d-%b-%Y')
			if j[0] == package_version:
				sexy_date = sexy_date + ' (Installed)'

			digits = len(str(package_number)) - 1

			# Packages already in the pacman cache are highlighted in green
			package_name = j[2].rsplit('/', 1)[1].replace('%2B', '+').replace('%3A', ':')
			if package_name in pacman_cache:
				template = "{0:%s}{1:%s}{2:%s}" % (3, 59 - digits, 15)
				print(template.format(colors.YELLOW + str(package_number) + ' ', colors.GREEN + j[0] + colors.ENDC, sexy_date))
			else:
				template = "{0:%s}{1:%s}{2:%s}" % (3, 50 - digits, 15)
				print(template.format(colors.YELLOW + str(package_number) + ' ' + colors.ENDC, j[0], sexy_date))

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
	if get_sig is True:
		sig_list = []
		for i in newphonewhodis:
			sig_list.append(i)
			sig_list.append(i + '.sig')
		newphonewhodis = sig_list

	for j in newphonewhodis:
		package_name = j.rsplit('/', 1)[1].replace('%2B', '+').replace('%3A', ':')
		if os.path.exists(user_def_dir):
			package_destination = user_def_dir + '/' + package_name
		else:
			package_destination = download_dir + '/' + package_name

		r1 = requests.head(j)
		file_size = int(r1.headers['Content-length'])
		file_size_MiB = file_size * 9.5367e-7
		print(colors.GREEN + package_name + ' (' + str(file_size_MiB)[:4] + ' MiB)' + colors.ENDC)

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


def main():
	global get_sig, user_def_dir, check_da_log_yo
	get_sig = False
	user_def_dir = ''
	check_da_log_yo = False

	parser = argparse.ArgumentParser(description='Download Arch Linux Archive packages from from your terminal. IT\'S THE FUTURE.')
	parser.add_argument('package_name', type=str, nargs='*', help='Package Name(s)')
	parser.add_argument('-d', type=str, nargs=1, help='Download directory', metavar='download_dir', required=False)
	parser.add_argument('--log', action='store_true', help='Show history from pacman.log', required=False)
	parser.add_argument('--sig', action='store_true', help='Get .sig files', required=False)
	args = parser.parse_args()

	if args.package_name:
		if args.d:
			user_def_dir = args.d
		if args.sig:
			get_sig = True
		if args.log:
			check_da_log_yo = True
		check_archive(args.package_name)
	else:
		parser.print_help()

main()
