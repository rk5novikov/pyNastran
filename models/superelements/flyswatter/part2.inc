$
$ part2.dat
$
CQUAD4	43	1	39	40	52	51
CQUAD4	44	1	40	41	53	52
CQUAD4	45	1	41	42	54	53
CQUAD4	46	1	42	43	55	54
CQUAD4	47	1	43	44	56	55
CQUAD4	48	1	51	52	64	63
CQUAD4	49	1	52	53	65	64
CQUAD4	50	1	53	54	66	65
CQUAD4	51	1	54	55	67	66
CQUAD4	52	1	55	56	68	67
CQUAD4	53	1	63	64	76	75
CQUAD4	54	1	64	65	77	76
CQUAD4	55	1	65	66	78	77
CQUAD4	56	1	66	67	79	78
CQUAD4	57	1	67	68	80	79
CQUAD4	58	1	75	76	88	87
CQUAD4	59	1	76	77	89	88
CQUAD4	60	1	77	78	90	89
CQUAD4	61	1	78	79	91	90
CQUAD4	62	1	79	80	92	91
CQUAD4	63	1	87	88	100	99
CQUAD4	64	1	88	89	101	100
CQUAD4	65	1	89	90	102	101
CQUAD4	66	1	90	91	103	102
CQUAD4	67	1	91	92	104	103
$
$		cp	a	b	c	cd	ps	seid
GRDSET							6
$
$ boundary grids
$
GRID	41		2.8	6.	0.
GRID	42		3.6	6.	0.
$
GRID	39		1.2	6.	0.
GRID	40		2.	6.	0.
GRID	43		4.4	6.	0.
GRID	44		5.2	6.	0.
$
GRID	51		1.2	6.8	0.
GRID	52		2.	6.8	0.
GRID	53		2.8	6.8	0.
GRID	54		3.6	6.8	0.
GRID	55		4.4	6.8	0.
GRID	56		5.2	6.8	0.
GRID	63		1.2	7.6	0.
GRID	64		2.	7.6	0.
GRID	65		2.8	7.6	0.
GRID	66		3.6	7.6	0.
GRID	67		4.4	7.6	0.
GRID	68		5.2	7.6	0.
GRID	75		1.2	8.4	0.
GRID	76		2.	8.4	0.
GRID	77		2.8	8.4	0.
GRID	78		3.6	8.4	0.
GRID	79		4.4	8.4	0.
GRID	80		5.2	8.4	0.
GRID	87		1.2	9.2	0.
GRID	88		2.	9.2	0.
GRID	89		2.8	9.2	0.
GRID	90		3.6	9.2	0.
GRID	91		4.4	9.2	0.
GRID	92		5.2	9.2	0.
GRID	99		1.2	10.	0.
GRID	100		2.	10.	0.
GRID	101		2.8	10.	0.
GRID	102		3.6	10.	0.
GRID	103		4.4	10.	0.
GRID	104		5.2	10.	0.
$
MAT1,1,30.+6,,.3,.283
PARAM,WTMASS,.00259
PARAM,AUTOSPC,YES
PSHELL,1,1,.05,1,,1
