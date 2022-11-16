

@timeclock.route("/", methods=["GET"])
def index():
    return "INDEX"


@auth.route("/login", methods=["GET", "POST"])
def login():
    return "LOGIN"
