import os

base_dir = 'logs'
sub_dirs = [
    'data_analyzer',
    'main',
]


os.makedirs(base_dir, exist_ok=True)
for sub_dir in sub_dirs:
    os.makedirs(os.path.join(base_dir, sub_dir), exist_ok=True)



logger_config = {
	'version': 1,
	'disable_existing_loggers': False,

	'formatters': {
		'std_format': {
            'format': '{asctime} - {levelname}:{funcName}:{lineno} -> {message}',
            'style': '{'
        },
	},
	'handlers': {
		'console': {
			'class': 'logging.StreamHandler',
			'level': 'DEBUG',
			'formatter': 'std_format'
		},
        'data_analyzer': {
			'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'filename': 'logs/data_analyzer/info_data_analyzer.log',
            'when': 'W0',
            'interval': 1,
            'backupCount': 4,
            'formatter': 'std_format'
		},
        'batch_analytics': {
			'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'filename': 'logs/main/info_batch_analytics.log',
            'when': 'W0',
            'interval': 1,
            'backupCount': 4,
            'formatter': 'std_format'
		},
        'main_logger': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'filename': 'logs/main/info_main.log',
            'when': 'W0',
            'interval': 1,
            'backupCount': 4,
            'formatter': 'std_format'
        },
        'trim_logger': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'filename': 'logs/main/info_trimming.log',
            'when': 'W0',
            'interval': 1,
            'backupCount': 4,
            'formatter': 'std_format'
        },
	},
    'loggers': {
		'data_analyzer_logger': {
			'level': 'INFO',
			'handlers': ['data_analyzer'],
			'propagate': False
		},
        'batch_analytics_logger': {
			'level': 'INFO',
			'handlers': ['batch_analytics'],
			'propagate': False
		},
        'main_logger': {
            'level': 'INFO',
            'handlers': ['main_logger'],
            'propagate': False
        },
        'trim_logger': {
            'level': 'INFO',
            'handlers': ['trim_logger'],
            'propagate': False
        },
	},
}