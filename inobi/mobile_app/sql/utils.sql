

CREATE OR REPLACE FUNCTION delete_user(user_id integer)
 RETURNS boolean
 LANGUAGE plpgsql
AS $$
declare login_id int;
declare social_user_id int;
begin
	if not exists(select 1 from users where id = user_id) then
		return false;
	end if;
	login_id = login from user_logins where "user" = user_id and type = 'login';
	delete from logins where id = login_id;
	social_user_id = login from user_logins where "user" = user_id and type = 'social_user';
	delete from social_users where id = social_user_id;
	delete from user_logins where "user" = user_id;
	delete from users where id = user_id; raise notice 'DELETED user: %, login: %, social_user: %', user_id, login_id, social_user_id;

	delete from transport_organization_drivers where "user" = user_id;
	delete from transport_organization_admins where "user" = user_id;

	return true;
end;
$$;
