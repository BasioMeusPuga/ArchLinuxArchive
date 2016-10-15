#!/usr/bin/python

import os
import requests
import argparse
import progressbar
import urllib.request

from bs4 import BeautifulSoup

ala = 'http://seblu.net/a/archive/packages/'
arch = 'x86_64'
download_dir = os.path.expanduser('~')


class colors:
	CYAN = '\033[96m'
	YELLOW = '\033[93m'
	GREEN = '\033[92m'
	RED = '\033[91m'
	WHITE = '\033[97m'
	ENDC = '\033[0m'


def check_archive(incoming_list):
	available_packages = {}

	for package in incoming_list:

		html = requests.get(ala + package[0] + '/' + package)

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

	display_shizz(available_packages)


def display_shizz(package_list):
	package_number = 1
	package_link_list = []

	for i in package_list:
		print(colors.CYAN + i.rjust(53) + colors.ENDC)
		for j in package_list[i]:
			if package_number < 10:
				template = "{0:%s}{1:%s}{2:%s}" % (3, 40, 15)
			else:
				template = "{0:%s}{1:%s}{2:%s}" % (3, 39, 15)
			print(template.format(colors.YELLOW + str(package_number) + ' ' + colors.ENDC, j[0], j[1]))
			package_link_list.append([i + ' ' + j[0], j[2]])
			package_number += 1

	download_me = input('Packages: ')
	entered_numbers = [int(k) for k in download_me.split()]

	download_list = []
	for l in entered_numbers:
		try:
			package_name = package_link_list[l - 1][0]
			package_link = package_link_list[l - 1][1]
			download_list.append([package_name, package_link])
		except:
			print('Are you sure? Like really really sure?')
			exit()

	download_packages(download_list)


def download_packages(newphonewhodis):

	def reporthook(blocknum, blocksize, totalsize):
		done = blocknum * blocksize
		bar = progressbar.ProgressBar(maxval=totalsize, widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), ' ', progressbar.ETA()])
		if done <= totalsize:
			bar.update(done)
		else:
			bar.update(totalsize)

	for i in newphonewhodis:
		package_name = i[1].rsplit('/', 1)[1].replace('%2B', '+')
		print(colors.GREEN + package_name + colors.ENDC)
		urllib.request.urlretrieve(i[1], download_dir + '/' + package_name, reporthook)
		print()

def main():

	parser = argparse.ArgumentParser(description='Download Arch Linux Archive packages from from your terminal. IT\'S THE FUTURE.')
	parser.add_argument('package_name', type=str, nargs='*', help='Package Name(s)')
	args = parser.parse_args()

	if args.package_name:
		check_archive(args.package_name)
	else:
		parser.print_help()

main()
