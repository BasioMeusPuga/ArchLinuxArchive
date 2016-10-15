#!/usr/bin/python

""" TODO
Parse pacman.log
"""

import os
import requests
import argparse
import collections
import progressbar

from bs4 import BeautifulSoup

ala = 'http://seblu.net/a/archive/packages/'
arch = 'x86_64'
download_dir = os.getcwd()


class colors:
	CYAN = '\033[96m'
	YELLOW = '\033[93m'
	GREEN = '\033[92m'
	RED = '\033[91m'
	WHITE = '\033[97m'
	ENDC = '\033[0m'


def check_archive(incoming_list, *args):
	available_packages = {}

	for package in incoming_list:

		html = requests.get(ala + package[0] + '/' + package)
		if html.status_code == 200:
			for i in html.iter_lines():
				link_line = BeautifulSoup(i.decode("utf-8"), "lxml")
				link_line_text = i.decode("utf-8").split()
				try:
					package_name_parsed = link_line.find('a').get('href')
					if arch in package_name_parsed and '.sig' not in package_name_parsed:
							package_name_full = package_name_parsed.split('-')

							package_name = package_name_full[0]
							package_version = package_name_full[1].replace('%2B', '+') + '-' + package_name_full[2]
							package_link = ala + package[0] + '/' + package_name + '/' + package_name_parsed

							try:
								available_packages[package_name].append([package_version, link_line_text[2], package_link])
							except KeyError:
								available_packages[package_name] = []
								available_packages[package_name].append([package_version, link_line_text[2], package_link])

				except:
					pass
		else:
			print(package + ':' + colors.RED + ' ' + str(html.status_code) + colors.ENDC)

	if len(available_packages) > 0:
		final_dict = collections.OrderedDict(sorted(available_packages.items(), key=lambda t: t[0]))
		display_shizz(final_dict)


def display_shizz(package_list):
	package_number = 1
	package_link_list = []

	for i in package_list:
		print(colors.CYAN + i.rjust(53) + colors.ENDC)
		for j in package_list[i]:
			
			digits = len(str(package_number)) - 1
			template = "{0:%s}{1:%s}{2:%s}" % (3, 40 - digits, 15)
			print(template.format(colors.YELLOW + str(package_number) + ' ' + colors.ENDC, j[0], j[1]))
			
			package_link_list.append([i + ' ' + j[0], j[2]])
			package_number += 1

	download_me = input('Packages: ')
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
		package_name = j.rsplit('/', 1)[1].replace('%2B', '+')
		if os.path.exists(user_def_dir):
			package_destination = user_def_dir + '/' + package_name
		else:
			package_destination = download_dir + '/' + package_name
		print(colors.GREEN + package_name + colors.ENDC)
		
		r1 = requests.head(j)
		file_size = int(r1.headers['Content-length'])
		bar = progressbar.ProgressBar(maxval=file_size, widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), ' ', progressbar.ETA()])
		r2 = requests.get(j, stream=True)
		
		downloaded = 0
		with open(package_destination, 'wb') as pdest:
			for chunk in r2.iter_content(100):
				pdest.write(chunk)
				downloaded += len(chunk)
				bar.update(downloaded)
		print()

def main():

	global get_sig
	global user_def_dir
	get_sig = False
	user_def_dir = ''

	parser = argparse.ArgumentParser(description='Download Arch Linux Archive packages from from your terminal. IT\'S THE FUTURE.')
	parser.add_argument('package_name', type=str, nargs='*', help='Package Name(s)')
	parser.add_argument('--sig', action='store_true', help='Get .sig files', required=False)
	parser.add_argument('-d', type=str, nargs=1, help='Download directory', metavar="download_dir", required=False)
	args = parser.parse_args()

	if args.package_name:
		if args.d:
			user_def_dir = args.d
		if args.sig:
			get_sig = True
		check_archive(args.package_name)
	else:
		parser.print_help()

main()
